"""One semantic identity/category boundary for preparing and validating visual evidence."""

import re

from garimpei.domain.listing.condition import normalized
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.repository.valuation.identity_mapper import current_identification

FAMILY_CATEGORIES = {
    "playstation5": "console",
    "xbox": "console",
    "switch": "console",
    "iphone": "electronics",
    "graphics_card": "electronics",
    "camera": "camera",
    "headphone": "headphone",
    "television": "television",
}


def assessment_context(listing: Listing) -> dict[str, object]:
    identity = current_identification(listing)
    observation = listing.latest
    assert observation is not None
    category = FAMILY_CATEGORIES.get(identity.family or "")
    if identity.state in {"conflicting_identity", "excluded_item"}:
        category = "unknown"
    if category is None:
        category = _category_for(str(observation.evidence.get("title") or ""))
    # Observation/revision and provenance remain in identity history. Only changes
    # to the effective evidence invalidate content reuse (including price-only observations).
    context: dict[str, object] = dict(
        state=identity.state,
        family=identity.family,
        attributes=[
            dict(name=name, value=value)
            for name, value in sorted({(a.name, a.value) for a in identity.attributes})
        ],
        missing_attributes=sorted(identity.missing_attributes),
        conflicts=sorted(c.review_key for c in identity.conflicts),
        policy=identity.policy_version,
    )
    return dict(category=category, identity=identity.product_key, identity_context=context)


def _category_for(title: str) -> str:
    value = normalized(title)
    patterns = [
        ("camera", r"\b(?:camera|canon|nikon)\b"),
        ("computer", r"\b(?:notebook|laptop|computador|macbook)\b"),
        ("console", r"\b(?:playstation|ps5|xbox|nintendo|console)\b"),
        ("headphone", r"\b(?:fone|headphone|headset)\b"),
        ("television", r"\b(?:tv|televisao|televisor)\b"),
        ("electronics", r"\b(?:iphone|celular|smartphone)\b"),
    ]
    matches = [category for category, pattern in patterns if re.search(pattern, value)]
    return matches[0] if len(matches) == 1 else "unknown"
