"""Conjunctive gold policy. F06/F07 remain the only estimators and money calculators."""

from dataclasses import replace
from datetime import datetime

from garimpei.domain.alert.gold_evidence import GoldDecision, GoldEvidence
from garimpei.domain.listing.condition import automatic_condition
from garimpei.domain.valuation.identification_values import IdentificationResult
from garimpei.domain.valuation.product_catalog import product_title

BLOCKED = frozenset(
    {
        "gold_condition_defect",
        "gold_condition_conflict",
        "gold_identity_conflict",
        "gold_item_incompatible",
        "gold_profit_non_positive",
    }
)


def canonical_name(identity: IdentificationResult) -> str:
    values = {attribute.name: attribute.value for attribute in identity.attributes}
    key = identity.product_key or ""
    if key.startswith("sony:ps5:"):
        parts = key.split(":")
        model = {"slim": "Slim", "pro": "Pro", "standard": ""}.get(parts[2], parts[2])
        edition = "com leitor" if parts[3] == "disc" else "digital"
        capacity = parts[4].replace("tb", " TB").replace("gb", " GB").upper()
        return " ".join(part for part in ("PlayStation 5", model, edition, capacity) if part)
    if identity.state == "identified":
        return " ".join(product_title(values).replace("gb", " GB").replace("tb", " TB").split())
    return key


def qualify(value: GoldEvidence, now: datetime, purpose_key: str = "first") -> GoldDecision:
    reasons = []
    if value.dependency_unavailable:
        reasons.append("gold_dependency_unavailable")
    if not value.applicable:
        reasons.append("gold_evidence_changed")
    reasons.extend(_condition(value))
    reasons.extend(_identity(value))
    reasons.extend(_history(value, now))
    reasons.extend(_profit(value))
    unique = tuple(dict.fromkeys(reasons)) or ("gold_qualified",)
    state = (
        "qualified" if not reasons else "blocked" if BLOCKED.intersection(reasons) else "waiting"
    )
    if unique[0] in {"gold_dependency_unavailable", "gold_evidence_changed"}:
        state = "waiting"
    return GoldDecision(
        value.listing_id,
        value.observation_id,
        purpose_key,
        value.fingerprint,
        state,
        unique,
        canonical_name(value.identity),
        value.identity.product_key,
        now,
        value.valuation.resale.valid_until if value.valuation else None,
    )


def _condition(value: GoldEvidence) -> tuple[str, ...]:
    assessment = value.assessment
    reasons = []
    if assessment.observation_id != value.observation_id:
        reasons.append("gold_evidence_changed")
    if not any(
        photo.get("examined") and photo.get("sha256") for photo in assessment.photo_coverage
    ):
        reasons.append("gold_photos_missing")
    result_reason = _assessment_reason(value)
    if result_reason:
        reasons.append(result_reason)
    if any(
        f.dimension == "identity" and f.assessment in {"conflict", "suspected"}
        for f in assessment.findings
    ):
        reasons.append("gold_condition_conflict")
    if automatic_condition(replace(value.text, condition=None)).condition != "good":
        reasons.append("gold_condition_insufficient")
    return tuple(reasons)


def _assessment_reason(value: GoldEvidence) -> str | None:
    assessment = value.assessment
    if assessment.status != "complete":
        return "gold_condition_pending"
    if assessment.condition == "defect" or value.effective_condition == "defect":
        return "gold_condition_defect"
    if (
        not assessment.sufficient
        or assessment.condition != "good"
        or value.effective_condition != "good"
    ):
        return "gold_condition_insufficient"
    return None


def _identity(value: GoldEvidence) -> tuple[str, ...]:
    identity = value.identity
    if value.text.source_available is not True:
        return ("gold_item_incompatible",)
    if (
        identity.observation_id != value.observation_id
        or identity.input_revision != value.observation_revision
    ):
        return ("gold_evidence_changed",)
    if identity.state == "conflicting_identity":
        return ("gold_identity_conflict",)
    if identity.state == "missing_attribute":
        return ("gold_identity_missing_attribute",)
    if identity.state in {"excluded_item", "unsupported_family"}:
        return ("gold_item_incompatible",)
    if identity.state != "identified" or not identity.product_key:
        return ("gold_identity_pending",)
    if value.valuation and value.valuation.product != identity.product_key:
        return ("gold_identity_conflict",)
    return ()


def _history(value: GoldEvidence, now: datetime) -> tuple[str, ...]:
    valuation = value.valuation
    if valuation is None:
        return ("gold_history_pending",)
    resale = valuation.resale
    if resale.valid_until is not None and now > resale.valid_until:
        return ("gold_history_expired",)
    if resale.reason == "amostra_dispersa":
        return ("gold_history_dispersed",)
    if resale.reason == "evidencia_vencida":
        return ("gold_history_expired",)
    if resale.price is None or resale.after < 5:
        return ("gold_history_insufficient",)
    if (
        valuation.input_revision != value.observation_revision
        or valuation.listing_id != value.listing_id
    ):
        return ("gold_evidence_changed",)
    if not resale.valid_until or valuation.method != "median-brl-v1":
        return ("gold_history_pending",)
    return ()


def _profit(value: GoldEvidence) -> tuple[str, ...]:
    financial = value.financial
    if financial is None:
        return ("gold_profit_pending",)
    if financial.listing_id != value.listing_id or financial.observation_id != value.observation_id:
        return ("gold_evidence_changed",)
    if value.valuation and (
        financial.evaluation_id != value.valuation.id
        or financial.evaluation_revision != value.valuation.revision
        or financial.resale != value.valuation.resale.price
    ):
        return ("gold_evidence_changed",)
    return ("gold_profit_non_positive",) if financial.profit <= 0 else ()
