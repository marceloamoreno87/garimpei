"""Measure five existing, complete F16 paths with owned PostgreSQL and fake channel."""

import json
import time
from pathlib import Path

from tests.factories.first_eligibility import first_eligibility_scenario
from tests.integration.test_collection import completed
from tests.integration.test_first_eligibility import wait_first


def measure_flows(directory: Path) -> list[dict[str, object]]:
    rows = []
    for repetition in range(5):
        private = directory / f"healthy-{repetition}"
        private.mkdir(mode=0o700, exist_ok=True)
        started = time.monotonic()
        with first_eligibility_scenario(private) as (instance, source, clock, channel):
            source.rows["16001"]["description"] = "Usado. Funciona perfeitamente."
            clock.advance(61)
            completed(instance, 2)
            wait_first(channel, clock)
            elapsed = time.monotonic() - started
            assert len(channel.messages) >= 1
            with instance.database() as database:
                sizes = database.execute("SELECT pg_database_size(current_database())").fetchone()
            rows.append(
                {
                    "stage": "complete_pipeline",
                    "repetition": repetition + 1,
                    "seconds_including_startup": elapsed,
                    "confirmed_receipts": len(channel.messages),
                    "database_bytes": sizes[0] if sizes else None,
                    "real_messages": 0,
                }
            )
    return rows


if __name__ == "__main__":
    directory = Path("/tmp/garimpei-f17-0d94-lab")
    (directory / "flow-calibration.json").write_text(
        json.dumps(measure_flows(directory), indent=2) + "\n"
    )
