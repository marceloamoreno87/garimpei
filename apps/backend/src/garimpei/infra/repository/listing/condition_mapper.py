from typing import cast

from garimpei.domain.listing.condition import Choice, ConditionState, automatic_condition
from garimpei.infra.persistence.listing_models import Listing, ManualCondition
from garimpei.infra.repository.listing.mapper import decode_evidence


def condition_state(row: Listing) -> ConditionState:
    manual: ManualCondition | None = getattr(row, "manual_condition", None)
    assert row.latest is not None
    return ConditionState(
        automatic_condition(decode_evidence(row.latest.evidence)),
        cast(Choice, manual.choice) if manual else None,
        manual.revision if manual else 0,
    )
