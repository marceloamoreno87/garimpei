import json
from uuid import uuid4

import pytest

from garimpei.domain.inference.errors import InferenceError
from garimpei.domain.inference.request import AnalysisInput, ImageReference
from garimpei.domain.inference.result import validate_result


def test_signature_separates_revision_and_artifacts() -> None:
    observation = uuid4()
    a = AnalysisInput(observation, 1, "Console íntegro", ())
    b = AnalysisInput(observation, 2, "Console íntegro", ())
    assert a.signature("sha256:" + "a" * 64) == a.signature("sha256:" + "a" * 64)
    assert a.signature("sha256:" + "a" * 64) != b.signature("sha256:" + "a" * 64)
    assert a.signature("sha256:" + "a" * 64) != a.signature("sha256:" + "b" * 64)


def test_images_are_part_of_signature_and_empty_evidence_is_refused() -> None:
    image = ImageReference("photo-a", 1, "a" * 64)
    a = AnalysisInput(uuid4(), 1, "", (image,))
    assert a.signature("model")
    with pytest.raises(InferenceError, match="insufficient_input"):
        AnalysisInput(uuid4(), 1, "", ())


@pytest.mark.parametrize("extra", [{"price": 100}, {"tool_calls": ["sh"]}, {"command": "send"}])
def test_structured_output_rejects_extra_actions_and_money(extra: dict[str, object]) -> None:
    value = {"findings": [], "unknowns": [], "limitations": [], **extra}
    with pytest.raises(InferenceError, match="invalid_output"):
        validate_result(json.dumps(value), "texto", ())


def test_evidence_must_match_exact_examined_material() -> None:
    result = {
        "findings": [
            {
                "description": "declaração",
                "references": [{"kind": "text", "start": 0, "end": 7, "quote": "íntegro"}],
            }
        ],
        "unknowns": [],
        "limitations": [],
    }
    assert validate_result(json.dumps(result), "íntegro", ()).findings
    with pytest.raises(InferenceError, match="invalid_output"):
        validate_result(json.dumps(result), "quebrou", ())
    result["findings"][0]["references"] = [{"kind": "image", "image_id": "unexamined"}]
    with pytest.raises(InferenceError, match="invalid_output"):
        validate_result(json.dumps(result), "", ("photo-a",))
