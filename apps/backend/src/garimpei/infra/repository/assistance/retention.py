"""F23 reviews gate candidates; F06 alone still selects its sample and median."""

from uuid import UUID

from garimpei.domain.valuation.values import Comparable
from garimpei.infra.persistence.assistance_models import AssistancePolicy
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.repository.assistance.publication import applicable_review, consume


def reviewed_candidates(
    target: Comparable, candidates: tuple[Comparable, ...], consumer: UUID | None = None
) -> tuple[tuple[Comparable, ...], list[str]]:
    if not AssistancePolicy.objects.filter(pk=1, active=True).exists():
        return candidates, []
    listing = Listing.objects.select_related("latest").get(id=target.listing_id)
    accepted, references = [], []
    for candidate in candidates:
        reference = _accepted(listing, candidate, consumer)
        if reference is not None:
            accepted.append(candidate)
            references.append(reference)
    return tuple(accepted), references


def _accepted(target: Listing, candidate: Comparable, consumer: UUID | None) -> str | None:
    row = Listing.objects.select_related("latest").filter(id=candidate.listing_id).first()
    if (
        row is None
        or row.latest is None
        or row.latest.ordinal != candidate.revision
        or target.latest_id is None
    ):
        return None
    review = applicable_review(target.latest_id, "comparables", row.latest_id)
    if review is None or review.state != "supported":
        return None
    findings = (review.result or {}).get("findings", [])
    if not any(
        f.get("field") == "equivalence" and f.get("value") == "equivalent" for f in findings
    ):
        return None
    if consumer is not None:
        consume(review, "valuation_work", str(consumer))
    return str(review.id)
