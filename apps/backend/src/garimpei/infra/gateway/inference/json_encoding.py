"""Canonical JSON wire formatting; strings and decoded schema/evidence remain unchanged."""

import json


def compact_json(value: object) -> str:
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False)
