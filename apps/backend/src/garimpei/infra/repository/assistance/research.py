from typing import cast

from garimpei.domain.listing.listing import Evidence
from garimpei.domain.valuation.identity import identify
from garimpei.infra.persistence.assistance_models import AssistanceReview
from garimpei.infra.persistence.monitoring_models import MonitoringInterest
from garimpei.infra.persistence.research_models import ComparableInvestigation
from garimpei.infra.repository.assistance.publication import consume, current_review


def apply_investigation_support(investigation: ComparableInvestigation) -> None:
    kind, _, key = investigation.origin_interest.partition(":")
    interest = MonitoringInterest.objects.filter(
        configuration_id=investigation.configuration_id, kind=kind, key=key
    ).first()
    if interest is None:
        return
    review = (
        AssistanceReview.objects.filter(
            target_kind="interest",
            target_id=interest.id,
            purpose="investigation",
            state="supported",
        )
        .order_by("-generation")
        .first()
    )
    if review is None or not current_review(review):
        return
    findings = cast(list[dict[str, object]], (review.result or {}).get("findings", []))
    terms = [str(f["value"]) for f in findings if f["field"] == "term"]
    # A suggested alias cannot broaden a precise comparable search to another variant.
    accepted = next(
        (
            term
            for term in terms
            if term == interest.label
            and identify(Evidence(title=term)) == investigation.product_key
        ),
        None,
    )
    if accepted is None:
        return
    investigation.term = accepted
    investigation.context = dict(investigation.context, assistance_review=str(review.id))
    investigation.save(update_fields=["term", "context"])
    consume(review, "investigation", str(investigation.id))
