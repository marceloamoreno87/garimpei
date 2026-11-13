"""Run actual navigation handlers against two interests, one persistently failing on loopback."""

import argparse
import json
import time
from pathlib import Path
from threading import Lock

import psutil
from tests.factories.listing import ControlledClock, serve
from tests.factories.navigation import NavigationSourceFake, prepare_navigation_instance
from tests.factories.runtime import pause_worker, resume_worker
from tests.integration.test_collection import command
from tests.integration.test_navigation import BOOTSTRAP


class FailingInterestSource(NavigationSourceFake):
    def __init__(self) -> None:
        super().__init__()
        self.lock = Lock()
        self.active = 0
        self.max_active = 0
        self.failed_calls = 0
        self.healthy_calls_after_failure = 0

    def respond(
        self, path: str, parameters: dict[str, str]
    ) -> tuple[int, dict[str, object]]:
        with self.lock:
            self.active += 1
            self.max_active = max(self.max_active, self.active)
        try:
            if path == "/search" and "iPhone" in parameters.get("term", ""):
                self.calls.append((path, parameters.copy()))
                self.failed_calls += 1
                context = {
                    key: value for key, value in parameters.items() if key != "page"
                }
                context["term"] = "unexpected-query"
                return 200, {
                    "context": context,
                    "cards": [],
                    "end": True,
                    "empty": True,
                    "next": None,
                }
            if self.failed_calls and path.startswith(("/search", "/detail/")):
                self.healthy_calls_after_failure += 1
            return super().respond(path, parameters)
        finally:
            with self.lock:
                self.active -= 1


STEP = """
import json
from garimpei.main import _navigation_collection,_effective_listing_settings,_listing_policy,build_listing_task_handler,build_read_monitoring_configuration,build_navigation_catalog
from garimpei.domain.listing.scope import Scope
from garimpei.infra.persistence.listing_models import CollectionState,ListingObservation
from garimpei.infra.persistence.operations_models import OperationalUnit
from garimpei.infra.persistence.navigation_models import NavigationWork
from garimpei.main import _listing_clock
settings=_effective_listing_settings()
collection=_navigation_collection(settings)
collection.reconcile(_listing_policy(settings))
state=CollectionState.objects.get()
for _ in range(8):
 state.refresh_from_db()
 build_listing_task_handler().execute(str(state.current_id),state.generation)
scope=Scope.from_snapshot(build_read_monitoring_configuration().execute())
assert scope
scope=build_navigation_catalog().decorate_scope(scope)
queries={query.term:query for query in scope.searches}
rows={key:OperationalUnit.objects.filter(stage='listing',scope=scope.key+':'+query.key).values('failures','suspended','reason','checkpoint','last_progress_at').first() for key,query in queries.items()}
print(json.dumps({'units':rows,'observations':list(ListingObservation.objects.values_list('listing__external_id',flat=True)),'failed_turn_deadlines':list(NavigationWork.objects.filter(reason='wrong_search_context').values_list('next_attempt_at',flat=True)),'at':_listing_clock(settings)()},default=str))
"""


def run(directory: Path) -> None:
    directory.mkdir(mode=0o700, parents=True, exist_ok=False)
    source = FailingInterestSource()
    clock = ControlledClock(directory / "clock")
    clock.advance(0)
    source.stamp = clock.value.isoformat()
    records = []
    started = time.monotonic()
    with serve(source) as url:
        instance = prepare_navigation_instance(Path.cwd().parents[1], directory, url)
        with instance.private_file.open("a") as output:
            output.write(
                f"GARIMPEI_LISTING_FIXTURE_CLOCK={clock.path}\nGARIMPEI_OPERATIONS_ENABLED=true\nGARIMPEI_BACKUP_DIR={directory / 'backups'}\n"
            )
        command(instance, "./scripts/init.sh", "--disposable")
        owner = next(
            row
            for row in instance.manifest["processes"]
            if "runworker" in row["command"]
        )
        listing_slots = [
            child
            for child in psutil.Process(owner["pid"]).children(recursive=True)
            if "--queue-group" in child.cmdline() and "listing" in child.cmdline()
        ]
        assert len(listing_slots) == 1
        group = pause_worker(instance)
        try:
            prepared = instance.shell(BOOTSTRAP)
            assert prepared.returncode == 0, prepared.stderr
            for _ in range(5):
                result = instance.shell(STEP)
                assert result.returncode == 0, result.stdout + result.stderr
                records.append(json.loads(result.stdout.strip().splitlines()[-1]))
                clock.advance(31)
            (directory / "interest-isolation-partial.json").write_text(
                json.dumps(
                    {"records": records, "failed_calls": source.failed_calls}, indent=2
                )
                + "\n"
            )
            units = records[-1]["units"]
            a = next(value for key, value in units.items() if "iPhone" in key)
            b = next(value for key, value in units.items() if "iPhone" not in key)
            assert a["failures"] == 1 and a["reason"] == "wrong_search_context"
            assert all(
                next(value for key, value in row["units"].items() if "iPhone" in key)[
                    "failures"
                ]
                == 1
                for row in records
            )
            assert records[0]["failed_turn_deadlines"]
            assert all(
                value > records[0]["at"]
                for value in records[0]["failed_turn_deadlines"]
            )
            assert not b["suspended"] and b["last_progress_at"]
            assert "1301" in records[-1]["observations"]
            before = source.failed_calls
            result = instance.shell(STEP)
            assert result.returncode == 0, result.stdout + result.stderr
            assert source.failed_calls == before
            assert source.healthy_calls_after_failure > 0
            assert source.max_active == 1
            assert time.monotonic() - started < 60
            elapsed = time.monotonic() - started
            report = {
                "item": "WRK-ISOLATION-01",
                "verdict": "PASS",
                "seconds_including_startup": elapsed,
                "interest_A": a,
                "interest_B": b,
                "confirmed_B_observation_ids": ["1301"],
                "failed_source_calls": source.failed_calls,
                "healthy_source_calls_after_failure": source.healthy_calls_after_failure,
                "additional_calls_while_given_attempt_waits": 0,
                "attempt_deadline_after_first_try": records[0]["failed_turn_deadlines"],
                "failure_counter_preserved": True,
                "recovery_budget_reference": "WRK-RECOVERY-01/03 separately verify the three-failure cap and restart persistence",
                "maximum_concurrent_source_calls": source.max_active,
                "reserved_listing_consumers": len(listing_slots),
                "scope": "Real Postgres/navigation task handler, loopback source; no real Facebook profile or credentials. The reserved listing slot and unchanged source-profile ownership guards enforce serialization.",
            }
            (directory / "interest-isolation.json").write_text(
                json.dumps(report, indent=2) + "\n"
            )
        finally:
            resume_worker(group)
            command(instance, "./scripts/stop.sh", "--clean")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    run(parser.parse_args().directory.resolve())
