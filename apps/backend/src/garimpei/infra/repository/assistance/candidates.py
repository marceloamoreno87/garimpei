"""Eligible equivalents have reserved capacity; exclusion review advances independently."""

from django.utils.timezone import now

from garimpei.domain.valuation.policy import eligible
from garimpei.infra.persistence.assistance_models import AssistanceReview
from garimpei.infra.persistence.listing_models import Listing, ListingObservation
from garimpei.infra.repository.assistance.publication import current_review
from garimpei.infra.repository.valuation.identity_mapper import current_identification
from garimpei.infra.repository.valuation.mapper import listing_comparable


def select_candidate_observations(target: Listing) -> list[ListingObservation]:
    key = current_identification(target).product_key
    if not key or target.latest_id is None:
        return []
    rows = (
        Listing.objects.exclude(id=target.id)
        .exclude(latest=None)
        .select_related("latest", "identity_progress__manual__observation")
        .order_by("id")
    )
    reviews = (
        AssistanceReview.objects.filter(purpose="comparables", observation_id=target.latest_id)
        .select_related("observation", "candidate_observation__listing")
        .order_by("-created_at")
    )
    reviewed: dict[str, bool] = {}
    for review in reviews:
        identity = str(review.candidate_observation_id)
        if identity not in reviewed:
            reviewed[identity] = current_review(review)
    plausible: list[ListingObservation] = []
    excluded: list[ListingObservation] = []
    point = now()
    for row in rows:
        if row.latest is None:
            continue
        value = listing_comparable(row, current_identification(row))
        destination = plausible if eligible(value, key, point) else excluded
        destination.append(row.latest)

    # Applicable history acts as a durable cursor: pending/finished contexts are not admitted twice.
    def order(observation: ListingObservation) -> tuple[bool, str]:
        return reviewed.get(str(observation.id), False), str(observation.listing_id)

    plausible.sort(key=order)
    excluded.sort(key=order)
    return [*plausible[:8], *excluded[:2]]
