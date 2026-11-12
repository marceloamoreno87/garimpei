import re
from collections import defaultdict
from dataclasses import replace
from uuid import UUID

from garimpei.domain.listing.condition import normalized
from garimpei.domain.listing.listing import Evidence
from garimpei.domain.valuation.identification_values import (
    AttributeConflict,
    IdentificationResult,
    IdentityAttribute,
)
from garimpei.domain.valuation.identity import identify
from garimpei.domain.valuation.identity_attributes import source_attributes
from garimpei.domain.valuation.manual_identity import ManualIdentity
from garimpei.domain.valuation.product_catalog import REQUIRED


def identify_product(
    evidence: Evidence,
    observation_id: UUID,
    input_revision: int,
    manual: ManualIdentity | None = None,
) -> IdentificationResult:
    title = normalized(evidence.title or "")
    if re.search(
        r"^(?:capa|capinha|pelicula|carregador|controle|jogo|suporte|lente|pecas?)\b|\blote\b",
        title,
    ):
        return IdentificationResult("excluded_item", observation_id, input_revision)
    product = identify(evidence)
    attributes = source_attributes(evidence, observation_id, input_revision, product)
    automatic_conflicts = _source_conflicts(attributes)
    family = next((a.value for a in attributes if a.name == "family"), None)
    if manual:
        return _manual_result(
            observation_id, input_revision, attributes, automatic_conflicts, manual
        )
    base = IdentificationResult(
        "unrecognized",
        observation_id,
        input_revision,
        family=family,
        attributes=_distinct(attributes),
    )
    if automatic_conflicts:
        return replace(base, state="conflicting_identity", conflicts=automatic_conflicts)
    if product:
        return replace(base, state="identified", product_key=product)
    if family:
        missing = tuple(
            name for name in REQUIRED[family] if name not in {a.name for a in attributes}
        )
        return replace(
            base,
            state="missing_attribute" if missing else "unsupported_family",
            missing_attributes=missing,
        )
    unsupported = re.search(
        r"\b(notebook|laptop|tablet|computador|impressora|smartwatch|microfone)\b", title
    )
    return replace(base, state="unsupported_family" if unsupported else "unrecognized")


def _manual_result(
    observation: UUID,
    revision: int,
    attributes: tuple[IdentityAttribute, ...],
    conflicts: tuple[AttributeConflict, ...],
    manual: ManualIdentity,
) -> IdentificationResult:
    values = dict(manual.values)
    contradictions = tuple(
        AttributeConflict(a.name, values[a.name], a.value, a.field, a.quote)
        for a in attributes
        if a.explicit and a.name in values and values[a.name] != a.value
    )
    unresolved = tuple(
        c for c in (*conflicts, *contradictions) if c.review_key not in manual.reviewed_conflicts
    )
    result = tuple(
        IdentityAttribute(
            name,
            value,
            "manual",
            manual.reviewed_observation_id or observation,
            manual.reviewed_revision,
            recorded_at=manual.recorded_at,
            reviewed_revision=manual.reviewed_revision,
        )
        for name, value in manual.values
    )
    return IdentificationResult(
        "conflicting_identity" if unresolved else "identified",
        observation,
        revision,
        values["family"],
        None if unresolved else manual.product_key,
        result,
        conflicts=unresolved,
        manual_revision=manual.revision,
    )


def _source_conflicts(attributes: tuple[IdentityAttribute, ...]) -> tuple[AttributeConflict, ...]:
    groups: dict[str, set[str]] = defaultdict(set)
    for attribute in attributes:
        if attribute.explicit:
            groups[attribute.name].add(attribute.value)
    return tuple(
        AttributeConflict(a.name, None, a.value, a.field, a.quote)
        for a in attributes
        if len(groups[a.name]) > 1
    )


def _distinct(attributes: tuple[IdentityAttribute, ...]) -> tuple[IdentityAttribute, ...]:
    first: dict[str, IdentityAttribute] = {}
    for attribute in attributes:
        first.setdefault(attribute.name, attribute)
    return tuple(first.values())
