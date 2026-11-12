"""Disposable integration UI lab; private inputs remain synthetic."""

import json
import tempfile
from pathlib import Path

from tests.factories.integration import integration_scenario
from tests.integration.test_collection import completed, configure


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="garimpei-f10-") as directory:
        with integration_scenario(Path(directory)) as (instance, source, clock, state, credentials):
            configure(instance)
            completed(instance, 1)
            metadata = {
                "url": f"http://127.0.0.1:{instance.config.web_port}",
                "environment_id": instance.config.environment_id,
            }
            output = instance.root / ".runtime/f10/lab.json"
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(metadata))
            print(json.dumps(metadata), flush=True)
            while True:
                action = json.loads(input())["action"]
                if action == "quit":
                    break
                if action == "paired":
                    state.phase, state.present = "WORKING", True
                if action == "expire":
                    source.mode = "access"
                    clock.advance(61)
                if action == "advance":
                    clock.advance(61)
                if action == "unavailable":
                    state.unavailable = True
                if action == "available":
                    state.unavailable = False
                print(json.dumps({"action": action, "phase": state.phase}), flush=True)


if __name__ == "__main__":
    main()
