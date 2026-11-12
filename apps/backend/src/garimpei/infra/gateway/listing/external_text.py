"""Represent malformed source prose without losing word boundaries or valid Unicode."""

import re

_UNREPRESENTABLE = re.compile(r"[\x00\ud800-\udfff]")


def evidence_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    # PostgreSQL text/JSONB cannot store NUL or unpaired Unicode surrogates. Mark the
    # damaged position rather than deleting it and accidentally joining words.
    result = _UNREPRESENTABLE.sub("\ufffd", value).strip()
    return result or None


def well_formed_text(value: str) -> bool:
    return _UNREPRESENTABLE.search(value) is None
