import json
from copy import deepcopy
from typing import cast

import pytest

from garimpei.domain.inference.condition_evidence import VERSION, validate_condition_result
from garimpei.domain.inference.errors import InferenceError

TEXT = json.dumps(
    dict(
        text=dict(title="Notebook Dell", description="Funciona perfeitamente.", condition="Usado"),
        category="computer",
        identity=None,
    )
)
VALID = dict(
    schema_version=VERSION,
    findings=[
        dict(
            dimension="appearance",
            assessment="light_wear",
            description="Riscos superficiais",
            references=[dict(kind="image", photo_id="p", sha256="a" * 64)],
        )
    ],
    conflicts=[],
    limitations=["Portas precisam de teste presencial"],
    examined_photos=[dict(photo_id="p", sha256="a" * 64)],
    omitted_photos=[],
)


def test_valid_photo_evidence_retains_source_hash_and_honest_limitations() -> None:
    assert validate_condition_result(json.dumps(VALID), TEXT, {"p": "a" * 64}) == VALID


@pytest.mark.parametrize(
    "fault",
    [
        "unknown_field",
        "enum",
        "quote",
        "photo",
        "hash",
        "omitted",
        "duplicate",
        "missing_reference",
    ],
)
def test_untraceable_or_malformed_output_cannot_support_condition(fault: str) -> None:
    value: dict[str, object] = cast(dict[str, object], deepcopy(VALID))
    finding = cast(list[dict[str, object]], value["findings"])[0]
    reference = cast(list[dict[str, object]], finding["references"])[0]
    if fault == "unknown_field":
        value["price"] = 1200
    elif fault == "enum":
        finding["assessment"] = "good"
    elif fault == "quote":
        finding["references"] = [dict(kind="text", field="description", quote="Nunca anunciado")]
    elif fault == "photo":
        reference["photo_id"] = "another"
    elif fault == "hash":
        reference["sha256"] = "b" * 64
    elif fault == "omitted":
        value["examined_photos"] = []
    elif fault == "duplicate":
        value["examined_photos"] = cast(list[object], value["examined_photos"]) * 2
    elif fault == "missing_reference":
        finding["references"] = []
    with pytest.raises(InferenceError, match="invalid_output"):
        validate_condition_result(json.dumps(value), TEXT, {"p": "a" * 64})
