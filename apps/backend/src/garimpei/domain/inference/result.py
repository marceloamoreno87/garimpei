import json
from dataclasses import dataclass
from typing import cast

from jsonschema import Draft202012Validator

from garimpei.domain.inference.errors import InferenceError

REFERENCE_SCHEMA: dict[str, object] = {
    "oneOf": [
        {
            "type": "object",
            "additionalProperties": False,
            "required": ["kind", "start", "end", "quote"],
            "properties": {
                "kind": {"const": "text"},
                "start": {"type": "integer", "minimum": 0},
                "end": {"type": "integer", "minimum": 1},
                "quote": {"type": "string", "minLength": 1, "maxLength": 500},
            },
        },
        {
            "type": "object",
            "additionalProperties": False,
            "required": ["kind", "image_id"],
            "properties": {
                "kind": {"const": "image"},
                "image_id": {"type": "string", "maxLength": 100},
            },
        },
    ]
}
SCHEMA: dict[str, object] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["findings", "unknowns", "limitations"],
    "properties": {
        "findings": {
            "type": "array",
            "maxItems": 8,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["description", "references"],
                "properties": {
                    "description": {"type": "string", "minLength": 1, "maxLength": 300},
                    "references": {
                        "type": "array",
                        "minItems": 1,
                        "maxItems": 4,
                        "items": REFERENCE_SCHEMA,
                    },
                },
            },
        },
        "unknowns": {
            "type": "array",
            "maxItems": 8,
            "items": {"type": "string", "minLength": 1, "maxLength": 300},
        },
        "limitations": {
            "type": "array",
            "maxItems": 8,
            "items": {"type": "string", "minLength": 1, "maxLength": 300},
        },
    },
}


@dataclass(frozen=True)
class AnalysisResult:
    findings: tuple[dict[str, object], ...]
    unknowns: tuple[str, ...]
    limitations: tuple[str, ...]


def validate_result(raw: str, text: str, images: tuple[str, ...]) -> AnalysisResult:
    try:
        value = json.loads(raw)
    except (TypeError, ValueError):
        raise InferenceError("invalid_output") from None
    if not Draft202012Validator(SCHEMA).is_valid(value):
        raise InferenceError("invalid_output")
    findings = cast(list[dict[str, object]], value["findings"])
    for finding in findings:
        _references(cast(list[dict[str, object]], finding["references"]), text, images)
    return AnalysisResult(tuple(findings), tuple(value["unknowns"]), tuple(value["limitations"]))


def _references(references: list[dict[str, object]], text: str, images: tuple[str, ...]) -> None:
    for reference in references:
        if reference["kind"] == "image" and reference["image_id"] not in images:
            raise InferenceError("invalid_output")
        if reference["kind"] == "image":
            continue
        start, end = cast(int, reference["start"]), cast(int, reference["end"])
        if start >= end or end > len(text) or text[start:end] != reference["quote"]:
            raise InferenceError("invalid_output")


def bounded_schema(text: str, image_id: str | None) -> dict[str, object]:
    schema = cast(dict[str, object], json.loads(json.dumps(SCHEMA)))
    properties = cast(dict[str, object], schema["properties"])
    findings = cast(dict[str, object], properties["findings"])
    item = cast(dict[str, object], findings["items"])
    fields = cast(dict[str, object], item["properties"])
    references = cast(dict[str, object], fields["references"])
    allowed: list[dict[str, object]] = []
    if image_id is not None:
        allowed = [{"kind": "image", "image_id": image_id}]
    else:
        allowed = [
            {
                "kind": "text",
                "start": start,
                "end": min(start + 240, len(text)),
                "quote": text[start : start + 240],
            }
            for start in range(0, len(text), 240)
        ]
    references["items"] = {"enum": allowed}
    return schema
