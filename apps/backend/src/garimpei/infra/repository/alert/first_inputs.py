"""Stable automatic evidence, shared by publication and manual-condition transactions."""

import hashlib
import json
from datetime import datetime
from uuid import UUID

from garimpei.domain.listing.listing import Evidence
from garimpei.domain.valuation.identification import identify_product
from garimpei.domain.valuation.identity import identify
from garimpei.infra.persistence.alert_models import FirstAlertIdentity
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.persistence.monitoring_models import MonitoringConfiguration
from garimpei.infra.persistence.valuation_models import ValuationWork
from garimpei.infra.repository.listing.mapper import decode_evidence
from garimpei.infra.repository.valuation.identity_mapper import current_identification


def automatic_signature(listing: Listing) -> str:
    observation = listing.latest
    if observation is None:
        return ""
    evidence = dict(observation.evidence)
    evidence.pop("image_url", None)
    evidence.pop("media", None)
    evidence.pop("freight", None)
    evidence.pop("freight_cep", None)
    for field in ("title", "description", "condition"):
        if isinstance(evidence.get(field), str):
            evidence[field] = " ".join(evidence[field].split()).casefold()
    work = ValuationWork.objects.filter(listing=listing).order_by("-revision").first()
    candidates = work.snapshot.get("candidates", []) if work else []
    valuation = semantic_candidates(candidates)
    configuration = (
        MonitoringConfiguration.objects.filter(slot="active").values("id", "revision").first()
    )
    value = dict(
        evidence=evidence,
        coverage=observation.coverage,
        interests=list(observation.matches.order_by("kind", "key").values_list("kind", "key")),
        valuation=valuation,
        configuration=configuration,
    )
    identity = current_identification(listing)
    automatic = identify_product(
        decode_evidence(observation.evidence), observation.id, observation.ordinal
    )
    if identity.manual_revision and (identity.state, identity.product_key) != (
        automatic.state,
        automatic.product_key,
    ):
        value["identity"] = dict(
            state=identity.state,
            product=identity.product_key,
            conflicts=sorted(c.review_key for c in identity.conflicts),
        )
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def invalidate_first_alert(listing_id: UUID, now: datetime) -> None:
    """Call in the publisher's transaction; the periodic repair also catches missed hooks."""
    FirstAlertIdentity.objects.filter(listing_id=listing_id).update(next_action=now)


def consume_manual_input(listing: Listing, now: datetime) -> None:
    signature = automatic_signature(listing)
    row, _ = FirstAlertIdentity.objects.select_for_update().get_or_create(
        listing=listing, defaults={"next_action": now}
    )
    row.manual_signature = signature
    row.next_action = min(row.next_action, listing.latest.observed_at if listing.latest else now)
    row.save(update_fields=["manual_signature", "next_action"])


def semantic_candidates(raw: object) -> list[dict[str, object]]:
    if not isinstance(raw, list):
        return []
    candidates = []
    for value in raw:
        if not isinstance(value, dict):
            continue
        candidate = {str(k): v for k, v in value.items() if k not in {"observed_at", "revision"}}
        identity = candidate.pop("identification", None)
        semantic = _manual_effect(identity, candidate.get("evidence"))
        if semantic is not None:
            candidate["identity"] = semantic
        if isinstance(candidate.get("evidence"), dict):
            evidence = dict(candidate["evidence"])
            evidence.pop("image_url", None)
            evidence.pop("media", None)
            candidate["evidence"] = evidence
        candidates.append(candidate)
    return sorted(candidates, key=lambda value: str(value.get("listing_id", "")))


def _manual_effect(identity: object, evidence: object) -> dict[str, object] | None:
    if not isinstance(identity, dict) or not identity.get("manual_revision"):
        return None
    raw = evidence if isinstance(evidence, dict) else {}
    title, description = raw.get("title"), raw.get("description")
    product = identify(
        Evidence(
            title=title if isinstance(title, str) else None,
            description=description if isinstance(description, str) else None,
        )
    )
    if identity.get("state") == "identified" and identity.get("product_key") == product:
        return None
    return {key: identity.get(key) for key in ("state", "product_key")}
