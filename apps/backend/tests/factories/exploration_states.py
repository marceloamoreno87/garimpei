"""Isolated F08 state lab. Actions are local files, never product routes."""

import json
import time
from pathlib import Path

from tests.factories.exploration import ExplorationSource, prepare_exploration_instance
from tests.factories.listing import ControlledClock, serve
from tests.factories.runtime import FoundationInstance
from tests.integration.test_collection import command


def main(directory: Path) -> None:
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    source = ExplorationSource(empty=True, pause_path="/search")
    with serve(source) as origin:
        i, clock = prepare_exploration_instance(
            Path(__file__).resolve().parents[4], directory, origin
        )
        command(i, "./scripts/init.sh", "--disposable")
        (directory / "public.json").write_text(
            json.dumps(dict(port=i.config.web_port, environment=i.config.environment_id))
        )
        print("State lab ready", i.config.web_port, flush=True)
        applied = ""
        try:
            while not (directory / "stop").exists():
                action = (
                    (directory / "action").read_text().strip()
                    if (directory / "action").exists()
                    else ""
                )
                if action and action != applied:
                    apply(action, source, i, clock)
                    applied = action
                    print("State action", action, flush=True)
                time.sleep(0.2)
        finally:
            source.release.set()
            command(i, "./scripts/stop.sh", "--clean")


def apply(
    action: str, source: ExplorationSource, i: "FoundationInstance", clock: "ControlledClock"
) -> None:
    if action == "configure":
        r = i.shell("from tests.factories.exploration import configure; configure()")
        assert r.returncode == 0, r.stdout + r.stderr
        return
    if action == "empty":
        source.pause_path = None
        source.release.set()
        return
    if action == "populate":
        source.empty = False
    if action == "partial":
        source.mode = "partial"
    if action == "fail":
        source.collection_failed = True
    if action == "interrupt":
        r = i.shell(
            "from tests.factories.monitoring import require_disposable; require_disposable(); from garimpei.infra.persistence.models import RuntimeState; from django.utils.timezone import now; RuntimeState.objects.all().update(stopped_at=now())"
        )
        assert r.returncode == 0
        return
    clock.advance(61)


if __name__ == "__main__":
    import sys

    main(Path(sys.argv[1]).resolve())
