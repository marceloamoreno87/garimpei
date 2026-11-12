from datetime import datetime

from garimpei.domain.valuation.policy import VALUATION_POLICY, eligible, estimate
from garimpei.domain.valuation.values import Comparable
from garimpei.infra.persistence.listing_models import Listing, ListingObservation
from garimpei.infra.persistence.research_models import (
    ComparableInvestigation,
    ResearchCandidateDecision,
    ResearchQuery,
)
from garimpei.infra.persistence.valuation_models import ValuationProgress
from garimpei.infra.repository.valuation.identity_mapper import identify_row
from garimpei.infra.repository.valuation.postgres_repository import _listing


def refresh_targets(row: ComparableInvestigation) -> bool:
    valid = False
    for target in row.targets.filter(active=True).select_related(
        "listing__latest", "listing__identity_progress__manual__observation"
    ):
        listing = target.listing
        current = identify_row(listing, getattr(listing, "identity_progress", None))
        fresh = (
            listing.latest_id == target.observation_id
            and current.state == "identified"
            and current.product_key == row.product_key
            and current.manual_revision == target.manual_revision
        )
        if not fresh:
            target.active = False
            target.save(update_fields=["active"])
        valid = valid or fresh
    return valid


def record_decisions(
    row: ComparableInvestigation,
    query: ResearchQuery,
    observation: ListingObservation,
    now: datetime,
) -> None:
    candidate = _listing(
        observation.listing,
        identify_row(observation.listing, getattr(observation.listing, "identity_progress", None)),
    )
    for target in row.targets.filter(active=True):
        same = target.listing_id == observation.listing_id
        accepted = not same and eligible(candidate, row.product_key, now)
        ResearchCandidateDecision.objects.get_or_create(
            query=query,
            target=target,
            observation=observation,
            policy=VALUATION_POLICY,
            defaults=dict(
                decision="accepted" if accepted else "excluded",
                reasons=[]
                if accepted
                else ["self" if same else exclusion(candidate, row.product_key, now)],
                evidence=dict(
                    eligibility_accepted=accepted,
                    product_key=candidate.product,
                    source=candidate.source,
                    external_id=candidate.external_id,
                    title=candidate.title,
                    price=str(candidate.price) if candidate.price is not None else None,
                    observed_at=candidate.observed_at.isoformat(),
                    revision=candidate.revision,
                    price_kind="announced",
                    url=candidate.url,
                    source_available=candidate.evidence.source_available,
                    published_at=candidate.evidence.published_at.isoformat()
                    if candidate.evidence.published_at
                    else None,
                    condition=candidate.evidence.condition,
                    description=candidate.evidence.description,
                ),
                recorded_at=now,
            ),
        )


def exclusion(candidate: Comparable, product: str, now: datetime) -> str:
    if candidate.product != product:
        return "different_identity"
    if candidate.price is None or candidate.price <= 0:
        return "price_unavailable"
    if (now - candidate.observed_at).total_seconds() > 14 * 86400:
        return "expired_observation"
    return "condition_installment_parts_or_uncertain"


def sufficient(row: ComparableInvestigation, now: datetime) -> bool:
    # Reuse F06, including deduplication, trimming and dispersion. This is not a second estimator.
    candidates = tuple(
        _listing(listing, identify_row(listing, getattr(listing, "identity_progress", None)))
        for listing in Listing.objects.select_related(
            "latest", "identity_progress__manual__observation"
        ).filter(source=row.context["source"], latest__isnull=False)
    )
    results = []
    for target in row.targets.filter(active=True).select_related(
        "listing__latest", "listing__identity_progress__manual__observation"
    ):
        listing = target.listing
        value = estimate(
            _listing(listing, identify_row(listing, getattr(listing, "identity_progress", None))),
            candidates,
            now,
        )
        _selection_history(row, target.id, value, now)
        results.append(value.price is not None)
        ValuationProgress.objects.filter(listing=listing).update(signature="", due_at=now)
    return bool(results) and all(results)


def _selection_history(
    row: ComparableInvestigation, target_id: "UUID", value: "Resale", now: datetime
) -> None:
    retained = {(c.listing_id, c.revision) for c in value.comparables}
    decisions = ResearchCandidateDecision.objects.filter(
        query__investigation=row, target_id=target_id, evidence__eligibility_accepted=True
    ).select_related("observation__listing")
    for decision in decisions:
        listing = decision.observation.listing
        accepted = (listing.id, decision.observation.ordinal) in retained
        stage = dict(
            retained=accepted,
            before=value.before,
            after=value.after,
            sample_reason=value.reason,
            calculated_at=now.isoformat(),
            policy=VALUATION_POLICY,
        )
        history = decision.evidence.setdefault("selection_history", [])
        if not history or history[-1] != stage:
            history.append(stage)
        decision.decision = "accepted" if accepted else "excluded"
        decision.reasons = (
            []
            if accepted
            else [
                "superseded_observation"
                if listing.latest_id != decision.observation_id
                else "outlier_50_150"
            ]
        )
        decision.save(update_fields=["evidence", "decision", "reasons"])


from uuid import UUID  # noqa: E402

from garimpei.domain.valuation.values import Resale  # noqa: E402
