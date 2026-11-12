from typing import cast

from garimpei.config.env import load_assessment_enabled
from garimpei.domain.listing.condition import Choice, ConditionState
from garimpei.domain.listing.condition_resolution import resolve_condition
from garimpei.infra.persistence.listing_models import Listing, ManualCondition
from garimpei.infra.queries.listing.assessment_queries import PostgresAssessmentQueries
from garimpei.infra.repository.listing.mapper import decode_evidence


def condition_state(row: Listing) -> ConditionState:
    manual: ManualCondition | None = getattr(row, "manual_condition", None)
    assert row.latest is not None
    assessment = (
        PostgresAssessmentQueries().observation(row.id, row.latest.id)
        if load_assessment_enabled()
        else None
    )
    return resolve_condition(
        decode_evidence(row.latest.evidence),
        assessment,
        cast(Choice, manual.choice) if manual else None,
        manual.revision if manual else 0,
    )
