"""Explicit F23 backup fields preserve revisions, typed targets and consumer traces."""

from django.db.models import Model

from garimpei.infra.persistence.assistance_models import (
    AssistanceCommand,
    AssistanceOperationsSnapshot,
    AssistancePolicy,
    AssistanceReview,
    AssistanceReviewRequest,
)

ASSISTANCE_SCHEMA: dict[str, tuple[type[Model], tuple[str, ...]]] = {
    "runtime.assistanceoperationssnapshot": (
        AssistanceOperationsSnapshot,
        ("revision", "content_hash", "facts", "whitelist_version", "created_at"),
    ),
    "runtime.assistancereview": (
        AssistanceReview,
        (
            "purpose",
            "target_kind",
            "target_id",
            "observation",
            "candidate_observation",
            "operations_snapshot",
            "input_signature",
            "generation",
            "input_snapshot",
            "state",
            "reason_code",
            "result",
            "consumed_by",
            "cache_reuses",
            "created_at",
            "updated_at",
            "completed_at",
        ),
    ),
    "runtime.assistancereviewrequest": (
        AssistanceReviewRequest,
        ("review", "request", "position"),
    ),
    "runtime.assistancecommand": (AssistanceCommand, ("command_hash", "review")),
    "runtime.assistancepolicy": (AssistancePolicy, ("active", "version", "adopted_at")),
}
