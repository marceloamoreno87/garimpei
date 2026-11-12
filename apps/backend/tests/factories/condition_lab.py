"""Reproducible, disposable F05 browser lab; JSON actions on stdin, no production flags.

Run from apps/backend: uv run --frozen --no-sync python -m tests.factories.condition_lab
Actions: status, update, collect, fail, clear_fault, reset_choices, restart, quit.
"""

import json
import tempfile
from pathlib import Path

from tests.factories.listing import (
    ConditionSource,
    clear_condition_fault,
    fail_next_condition_write,
    prepare_listing_instance,
    serve,
)
from tests.integration.test_collection import command, completed, configure, sql


def main() -> None:
    root = Path(__file__).resolve().parents[4]
    source = ConditionSource()
    with tempfile.TemporaryDirectory(prefix="garimpei-f05-") as private, serve(source) as url:
        instance, clock = prepare_listing_instance(root, Path(private), url)
        command(instance, "./scripts/init.sh", "--disposable")
        try:
            configure(instance)
            completed(instance, 1)
            count = 1
            metadata = {
                "url": f"http://127.0.0.1:{instance.config.web_port}",
                "environment_id": instance.config.environment_id,
                "private_file": str(instance.private_file),
                "ids": {
                    str(row[0]): str(row[1])
                    for row in sql(instance, "SELECT external_id,id::text FROM runtime_listing")
                },
            }
            (root / ".runtime/f05/lab.json").write_text(json.dumps(metadata))
            print(json.dumps(metadata), flush=True)
            while True:
                action = json.loads(input())
                name = action["action"]
                if name == "quit":
                    break
                if name == "update":
                    source.rows[action["key"]].update(action["fields"])
                if name == "source_failure":
                    source.failed = action["failed"]
                if name == "collect":
                    clock.advance(61)
                    count += 1
                    completed(instance, count, "unavailable" if source.failed else "complete")
                if name == "fail":
                    fail_next_condition_write(instance, action.get("delay", 0))
                if name == "clear_fault":
                    clear_condition_fault(instance)
                if name == "reset_choices":
                    sql(instance, "DELETE FROM runtime_manualconditionhistory")
                    sql(instance, "DELETE FROM runtime_manualcondition")
                if name == "restart":
                    command(instance, "./scripts/stop.sh")
                    clock.advance(61)
                    command(instance, "./scripts/init.sh", "--disposable")
                    count += 1
                    completed(instance, count)
                print(
                    json.dumps(
                        {
                            "action": name,
                            "cycles": count,
                            "choices": sql(
                                instance,
                                "SELECT listing_id::text,choice,revision FROM runtime_manualcondition",
                            ),
                            "events": sql(
                                instance,
                                "SELECT id::text,kind FROM runtime_listingevent ORDER BY sequence",
                            ),
                            "listing_jobs": sql(
                                instance,
                                "SELECT id FROM procrastinate_jobs WHERE queue_name='listing' ORDER BY id",
                            ),
                        }
                    ),
                    flush=True,
                )
        finally:
            command(instance, "./scripts/stop.sh", "--clean")


if __name__ == "__main__":
    main()
