"""Run in a frozen checkout's apps/backend; use only owned eval resources and loopback."""

import argparse
import json
import time
from datetime import timedelta
from pathlib import Path

from tests.factories.alert_scenario import alert_scenario, wait_alerts
from tests.factories.operations_metrics import InstanceMeasurements, workload_signature
from tests.factories.valuation import listing
from tests.integration.test_collection import completed, sql, wait_for


def run_pair(directory: Path, repetition: int, blocked: bool) -> dict[str, object]:
    mode = "fault" if blocked else "control"
    private = directory / f"{repetition}-{mode}"
    private.mkdir(mode=0o700)
    report = private / "measurements.json"
    with alert_scenario(private) as (instance, source, clock, channel):
        with instance.private_file.open("a") as output:
            output.write(
                f"GARIMPEI_BACKUP_DIR={private / 'backups'}\nGARIMPEI_OPERATIONS_ENABLED=true\n"
            )
        with InstanceMeasurements(instance, report, mode=mode) as metrics:
            channel.hold_post = blocked
            baseline_clock = clock.value
            clock.advance(1)
            source.rows["17931"] = listing(
                "17931",
                "1000,00",
                published_at=(baseline_clock + timedelta(seconds=1)).isoformat(),
                delivery=True,
                delivery_cep="01001000",
                pickup=False,
            )
            clock.advance(61)
            completed(instance, 2)
            if blocked:
                assert channel.held.wait(15), "owned channel did not hold the POST"
            else:
                wait_alerts(instance, 1, clock)
            independent_started = time.monotonic()
            baseline = sql(
                instance,
                "SELECT count(*) FROM runtime_collectioncycle WHERE finished_at IS NOT NULL",
            )[0][0]
            clock.advance(1)
            source.pause_path = "/new" if blocked else None
            source.rows["17932"] = listing(
                "17932",
                "1000,00",
                published_at=(baseline_clock + timedelta(seconds=124)).isoformat(),
                delivery=True,
                delivery_cep="01001000",
                pickup=False,
            )
            clock.advance(61)
            if blocked:
                assert source.held.wait(8), "owned valuation did not block"
            probe = instance.command(
                "uv",
                "run",
                "--project",
                "apps/backend",
                "--frozen",
                "--no-sync",
                "python",
                "apps/backend/manage.py",
                "runtime_probe",
                "--wait",
                timeout=12,
            )
            assert probe.returncode == 0, "independent runtime probe did not finish"
            maintenance = instance.shell(
                "from garimpei.main import reconcile_operations;reconcile_operations()"
            )
            assert maintenance.returncode == 0, "maintenance request was not accepted"
            wait_for(
                lambda: bool(
                    sql(
                        instance,
                        "SELECT id FROM runtime_backuprecord WHERE kind='backup' AND state='completed'",
                    )
                ),
                "independent backup while channel busy",
                seconds=10,
            )
            wait_for(
                lambda: (
                    int(
                        sql(
                            instance,
                            "SELECT count(*) FROM runtime_collectioncycle WHERE finished_at IS NOT NULL",
                        )[0][0]
                    )
                    > int(baseline)
                ),
                "independent collection while channel busy",
                seconds=10,
            )
            elapsed = time.monotonic() - independent_started
            if blocked:
                assert elapsed < 9, (
                    "independent progress only arrived after channel timeout"
                )
                assert not channel.release.is_set()
                assert (
                    sql(
                        instance,
                        "SELECT count(*) FROM runtime_alertintent WHERE state='authorized'",
                    )[0][0]
                    >= 1
                )
            source.pause_path = None
            source.release.set()
            channel.release.set()
            channel.hold_post = False
            wait_alerts(instance, 2, clock)
            assert len(channel.messages) == 2
            assert len([call for call in channel.calls if call[0] == "POST"]) == 2
            metrics.observed.update(
                offers=2,
                held_stages=2 if blocked else 0,
                confirmed_posts=2,
                independent_progress_milliseconds=int(elapsed * 1000),
                workload_signature=workload_signature(source.rows),
            )
    return json.loads(report.read_text())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    options = parser.parse_args()
    directory = options.directory.resolve()
    directory.mkdir(mode=0o700, parents=True, exist_ok=False)
    results = []
    for repetition in range(1, 6):
        pair = {
            mode: run_pair(directory, repetition, mode == "fault")
            for mode in ("control", "fault")
        }
        assert (
            pair["control"]["workload_signature"] == pair["fault"]["workload_signature"]
        )
        results.append({"repetition": repetition, **pair})
        (directory / "isolation.json").write_text(
            json.dumps({"measurements": results, "profile_confirmed": False}, indent=2)
            + "\n"
        )


if __name__ == "__main__":
    main()
