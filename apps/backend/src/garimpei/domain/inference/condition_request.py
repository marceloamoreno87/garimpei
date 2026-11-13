"""Short physical references expand losslessly; consumers still validate the canonical evidence."""

import json
from copy import deepcopy
from typing import cast

from jsonschema import Draft202012Validator

from garimpei.domain.inference.condition_evidence import SCHEMA, validate_condition_result
from garimpei.domain.inference.errors import InferenceError


def _reference_table(
    text: str, photo_id: str | None, sha256: str | None
) -> dict[str, dict[str, object]]:
    try:
        fields = json.loads(text)["text"]
    except (ValueError, KeyError, TypeError):
        raise InferenceError("invalid_output", diagnostic="invalid_reference_context") from None
    if not isinstance(fields, dict):
        raise InferenceError("invalid_output", diagnostic="invalid_reference_context")
    texts: list[dict[str, object]] = []
    for field in ("title", "description", "condition"):
        source = fields.get(field)
        if isinstance(source, str):
            texts.extend(
                dict(kind="text", field=field, quote=source[start : start + 240])
                for start in range(0, len(source), 240)
            )
    result = {f"t{index}": reference for index, reference in enumerate(texts)}
    if photo_id is not None:
        result["i0"] = dict(kind="image", photo_id=photo_id, sha256=sha256)
    return result


def condition_schema(text: str, photo_id: str | None, sha256: str | None) -> dict[str, object]:
    table = _reference_table(text, photo_id, sha256)
    schema = deepcopy(SCHEMA)
    properties = cast(dict[str, dict[str, object]], schema["properties"])
    schema["$defs"] = {
        "references": {
            "type": "array",
            "minItems": 1,
            "maxItems": 4,
            "items": {"enum": list(table)} if table else False,
        }
    }
    for field in ("findings", "conflicts"):
        item = cast(dict[str, object], properties[field]["items"])
        fields = cast(dict[str, object], item["properties"])
        fields["references"] = {"$ref": "#/$defs/references"}
    properties.pop("examined_photos")
    properties.pop("omitted_photos")
    schema["required"] = ["schema_version", "findings", "conflicts", "limitations", "photo"]
    status_schema: dict[str, object] = (
        {"enum": ["examined", "omitted"]} if photo_id else {"const": "not_provided"}
    )
    properties["photo"] = {
        "type": "object",
        "additionalProperties": False,
        "required": ["status", "reason"],
        "properties": {
            "status": status_schema,
            "reason": {"type": "string", "minLength": 1, "maxLength": 300},
        },
    }
    return schema


def condition_content(text: str, photo_id: str | None, sha256: str | None = None) -> str:
    table: dict[str, object] = dict(_reference_table(text, photo_id, None))
    if photo_id is not None:
        table["i0"] = "única foto atual"
    # Original text is untouched. Codes eliminate model-generated hashes and approximate quotations.
    return (
        text
        + "\nCódigos de referência: "
        + json.dumps(table, ensure_ascii=False, separators=(",", ":"))
        + "\nSchema: "
        + json.dumps(
            condition_schema(text, photo_id, sha256), ensure_ascii=False, separators=(",", ":")
        )
    )


def decode_condition_content(
    raw: object, text: str, photo_id: str | None, sha256: str | None
) -> str:
    try:
        value = json.loads(raw) if isinstance(raw, str) else None
    except ValueError:
        raise InferenceError("invalid_output", diagnostic="invalid_json_or_context") from None
    if not isinstance(value, dict) or not Draft202012Validator(
        condition_schema(text, photo_id, sha256)
    ).is_valid(value):
        raise InferenceError("invalid_output", diagnostic="schema_mismatch")
    table = _reference_table(text, photo_id, sha256)
    for record in value["findings"] + value["conflicts"]:
        record["references"] = [table[code] for code in record["references"]]
    photo = value.pop("photo")
    value["examined_photos"] = (
        [dict(photo_id=photo_id, sha256=sha256)] if photo["status"] == "examined" else []
    )
    value["omitted_photos"] = (
        [dict(photo_id=photo_id, reason=photo["reason"])] if photo["status"] == "omitted" else []
    )
    canonical = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    validate_condition_result(canonical, text, {photo_id: str(sha256)} if photo_id else {})
    return canonical
