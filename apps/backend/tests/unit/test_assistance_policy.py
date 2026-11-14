import json
from copy import deepcopy
from typing import cast

import pytest

from garimpei.domain.assistance.review import PROFILES, validate_assistance_output
from garimpei.domain.inference.errors import InferenceError
from tests.factories.assistance import identity_snapshot, supported_response


def test_supported_identity_requires_exact_current_source_excerpt() -> None:
    output = supported_response()
    assert (
        validate_assistance_output(
            PROFILES["identity"], json.dumps(output), json.dumps(identity_snapshot())
        )
        == output
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "reference",
        "value",
        "extra-key",
        "tool-call",
        "missing-field",
        "wrong-quote",
        "bad-offset",
        "photo-not-examined",
        "unsupported-source",
        "conflict",
        "unknown-value",
    ],
)
def test_hostile_or_unsupported_confirmation_is_rejected(mutation: str) -> None:
    snapshot, output = deepcopy(identity_snapshot()), deepcopy(supported_response())
    finding = cast(list[dict[str, object]], output["findings"])[0]
    fact = cast(list[dict[str, object]], snapshot["facts"])[0]
    if mutation == "reference":
        finding["evidence_refs"] = ["invented"]
    elif mutation == "value":
        finding["value"] = "ps6"
    elif mutation == "extra-key":
        finding["price"] = "1000"
    elif mutation == "tool-call":
        output["tool_calls"] = [{"name": "send_message"}]
    elif mutation == "missing-field":
        snapshot["required_fields"] = ["model", "capacity"]
    elif mutation == "wrong-quote":
        fact["quote"] = "invented seller declaration"
    elif mutation == "bad-offset":
        fact["end"] = 999999
    elif mutation == "photo-not-examined":
        fact["source"] = "image"
    elif mutation == "unsupported-source":
        fact["source"] = "system"
    elif mutation == "conflict":
        snapshot["conflict"] = True
    else:
        snapshot["allowed_values"] = {"model": []}
    with pytest.raises(InferenceError, match="invalid_output"):
        validate_assistance_output(PROFILES["identity"], json.dumps(output), json.dumps(snapshot))


def test_insufficient_result_can_abstain_without_fabricating_an_attribute() -> None:
    output = dict(outcome="insufficient", findings=[], limitations=["Capacity not observed"])
    assert (
        validate_assistance_output(
            PROFILES["identity"], json.dumps(output), json.dumps(identity_snapshot())
        )["outcome"]
        == "insufficient"
    )


def test_unknown_evidence_cannot_be_promoted_by_supported_outcome() -> None:
    snapshot = identity_snapshot() | {"confirmation_allowed": False}
    with pytest.raises(InferenceError, match="invalid_output"):
        validate_assistance_output(
            PROFILES["comparables"], json.dumps(supported_response()), json.dumps(snapshot)
        )
