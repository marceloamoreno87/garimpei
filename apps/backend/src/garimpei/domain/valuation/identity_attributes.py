"""Literal source spans, with explicitness separate from catalog-derived defaults."""

import re
from uuid import UUID

from garimpei.domain.listing.listing import Evidence
from garimpei.domain.valuation.component_identity import CAMERA_MODELS
from garimpei.domain.valuation.identification_values import IdentityAttribute
from garimpei.domain.valuation.product_catalog import product_values

FAMILIES = (
    ("playstation5", r"\b(?:playstation\s*5|ps5)\b"),
    ("iphone", r"\biphone\b"),
    ("xbox", r"\bxbox\s*series\b"),
    ("switch", r"\b(?:nintendo\s*)?switch\b"),
    ("graphics_card", r"\brtx\s*\d{4}\b"),
    ("camera", r"\b(?:c[aâ]mera|canon|nikon|a6000|a6300|a6400)\b"),
    ("television", r"\b(?:tv|televis[aã]o|televisor|un\d{2}[a-z]{2}\d{4}[a-z]{4})\b"),
    ("headphone", r"\b(?:fone|headphone|wh[-\s]?1000xm\d+|tune\s*\d+bt)\b"),
)


def source_attributes(
    evidence: Evidence, observation: UUID, revision: int, product: str | None
) -> tuple[IdentityAttribute, ...]:
    result: list[IdentityAttribute] = []
    for field, text in (
        ("title", evidence.title or ""),
        ("description", evidence.description or ""),
    ):
        result.extend(_family_attributes(text, field, observation, revision))
        families = {a.value for a in result if a.name == "family"}
        for family in families:
            result.extend(_field_attributes(family, text, field, observation, revision))
    return _complete(result, product, observation, revision)


def _complete(
    result: list[IdentityAttribute], product: str | None, observation: UUID, revision: int
) -> tuple[IdentityAttribute, ...]:
    if not product:
        return tuple(result)
    values = product_values(product)
    fallback = next(iter(result), None)
    for name, value in values.items():
        if not any(a.name == name for a in result) and fallback:
            result.append(
                IdentityAttribute(
                    name,
                    value,
                    "automatic",
                    observation,
                    revision,
                    fallback.field,
                    fallback.quote,
                    explicit=False,
                )
            )
    return tuple(result)


def _family_attributes(
    text: str, field: str, observation: UUID, revision: int
) -> tuple[IdentityAttribute, ...]:
    return tuple(
        IdentityAttribute(
            "family", family, "automatic", observation, revision, field, match.group()
        )
        for family, pattern in FAMILIES
        for match in re.finditer(pattern, text, re.I)
    )


def _field_attributes(
    family: str, text: str, field: str, observation: UUID, revision: int
) -> tuple[IdentityAttribute, ...]:
    values: list[tuple[str, str, str]] = []
    if family == "playstation5":
        values += _values(text, "model", r"\b(?:playstation\s*5|ps5)\b", fixed="ps5")
        values += _values(text, "generation", r"\b(slim|fat|pro)\b")
        values += _values(
            text,
            "edition",
            r"com leitor|c/\s*leitor|m[ií]dia f[ií]sica|vers[aã]o disco|\bdisco\b|\bdisk\b",
            fixed="disc",
        )
        values += _values(
            text,
            "edition",
            r"edi[cç][aã]o digital|slim digital|m[ií]dia digital|digital edition",
            fixed="digital",
        )
    if family == "iphone":
        values += _values(text, "model", r"\biphone\s*(11|12|13|14|15|16)\b", group=1)
        values += _values(text, "edition", r"\b(pro\s*max|pro|mini|plus)\b")
    if family == "xbox":
        values += _values(text, "model", r"\bxbox\s*(series\s*[sx])\b", group=1)
        values += _values(text, "edition", r"com leitor|m[ií]dia f[ií]sica|\bdisco\b", fixed="disc")
        values += _values(text, "edition", r"digital|sem leitor", fixed="digital")
    if family == "switch":
        values += _values(text, "model", r"\bswitch\b", fixed="switch")
        values += _values(text, "generation", r"\bswitch\s*(oled|lite|v1|v2)\b", group=1)
    if family == "graphics_card":
        values += _values(text, "model", r"\brtx\s*(\d{4}\s*(?:ti\s*super|super|ti)?)\b", group=1)
        values += _values(text, "memory_type", r"\bgddr\s*6x?\b")
    if family == "camera":
        values += _values(text, "brand", r"\b(canon|nikon|sony)\b")
        for pattern in CAMERA_MODELS.values():
            values += _values(text, "model", pattern, group=1)
        values += _values(
            text,
            "edition",
            r"somente corpo|apenas corpo|s[oó] (?:o )?corpo|body only|corpo sem lente",
            fixed="body",
        )
    if family == "television":
        values += _values(text, "brand", r"\b(samsung|lg)\b")
        values += _values(
            text, "model", r"\bun\d{2}[a-z]{2}\d{4}[a-z]{4}\b|\b\d{2}ur\d{4}[a-z]{3}\.[a-z]{3}\b"
        )
    if family == "headphone":
        values += _values(text, "brand", r"\b(sony|jbl)\b")
        values += _values(text, "model", r"\b(?:wh[-\s]?1000xm\d+[a-z]*|tune\s*\d+[a-z]+)\b")
    if family in {"playstation5", "iphone", "xbox", "switch", "graphics_card"}:
        values += _values(text, "capacity", r"(?<!\d)(?:\d{1,4}\s*gb|[1-9]\s*tb|[1-9]\s*tera)\b")
    return tuple(
        IdentityAttribute(name, value, "automatic", observation, revision, field, quote)
        for name, value, quote in values
    )


def _values(
    text: str, name: str, pattern: str, *, fixed: str | None = None, group: int = 0
) -> list[tuple[str, str, str]]:
    return [
        (
            name,
            fixed or re.sub(r"[-\s]", "", match.group(group).casefold()).replace("tera", "tb"),
            match.group(),
        )
        for match in re.finditer(pattern, text, re.I)
    ]
