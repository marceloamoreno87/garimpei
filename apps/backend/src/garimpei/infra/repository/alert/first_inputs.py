"""Stable automatic evidence, shared by publication and manual-condition transactions."""

import hashlib
import json
from datetime import datetime
from uuid import UUID

from garimpei.infra.persistence.alert_models import FirstAlertIdentity
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.persistence.monitoring_models import MonitoringConfiguration
from garimpei.infra.persistence.valuation_models import ValuationWork


def automatic_signature(listing: Listing) -> str:
    observation = listing.latest
    if observation is None:
        return ""
    evidence = dict(observation.evidence)
    evidence.pop("image_url", None)
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
        if isinstance(candidate.get("evidence"), dict):
            evidence = dict(candidate["evidence"])
            evidence.pop("image_url", None)
            candidate["evidence"] = evidence
        candidates.append(candidate)
    return sorted(candidates, key=lambda value: str(value.get("listing_id", "")))
