from typing import cast
from uuid import UUID

from garimpei.infra.persistence.assistance_models import AssistancePolicy
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.repository.assistance.publication import applicable_review, consume


def qualification_reviews(
    listing: Listing, record: dict[str, object]
) -> tuple[list[str], list[str]]:
    if not AssistancePolicy.objects.filter(pk=1, active=True).exists():
        return [], []
    review = applicable_review(listing.latest_id, "identity") if listing.latest_id else None
    missing = []
    references = []
    if review is None or review.state != "supported":
        missing.append("assistance_identity_pending")
    else:
        references.append(str(review.id))
        consume(review, "gold_qualification", str(listing.id))
    valuation = cast(dict[str, object], record.get("valuation") or {})
    resale = cast(dict[str, object], valuation.get("resale") or {})
    for comparable in cast(list[dict[str, object]], resale.get("comparables", [])):
        _candidate(listing, comparable, missing, references)
    record["assistance"] = dict(policy="assisted-evidence-v1", reviews=references, missing=missing)
    return missing, references


def _candidate(
    listing: Listing, comparable: dict[str, object], missing: list[str], references: list[str]
) -> None:
    candidate = (
        Listing.objects.select_related("latest")
        .filter(id=UUID(str(comparable["listing_id"])))
        .first()
    )
    review = (
        applicable_review(listing.latest_id, "comparables", candidate.latest_id)
        if listing.latest_id and candidate
        else None
    )
    matched = bool(
        candidate
        and candidate.latest
        and candidate.latest.ordinal == int(str(comparable["revision"]))
    )
    findings = (
        cast(list[dict[str, object]], (review.result or {}).get("findings", [])) if review else []
    )
    if (
        not matched
        or review is None
        or review.state != "supported"
        or not any(
            f.get("field") == "equivalence" and f.get("value") == "equivalent" for f in findings
        )
    ):
        missing.append("assistance_comparable_pending")
        return
    references.append(str(review.id))
    consume(review, "comparable_retention", str(listing.id))
