from typing import cast

from garimpei.domain.listing.assessment import Assessment
from garimpei.domain.listing.condition import (
    Analysis,
    Choice,
    Condition,
    ConditionState,
    automatic_condition,
)
from garimpei.domain.listing.listing import Evidence


def resolve_condition(
    evidence: Evidence,
    assessment: Assessment | None,
    manual: Choice | None = None,
    revision: int = 0,
) -> ConditionState:
    text = automatic_condition(evidence)
    if assessment is None:
        return ConditionState(text, manual, revision)
    condition = "defect" if text.condition == "defect" else assessment.condition
    return ConditionState(
        Analysis(cast(Condition, condition), text.signals, text.reasons),
        manual,
        revision,
        assessment,
    )
