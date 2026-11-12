"""Explicit recovery fields for multimodal evidence and its current observation link."""

from django.db.models import Model

from garimpei.infra.persistence.assessment_models import AssessmentHead, ConditionAssessment

ASSESSMENT_SCHEMA: dict[str, tuple[type[Model], tuple[str, ...]]] = {
    "runtime.conditionassessment": (
        ConditionAssessment,
        (
            "listing",
            "observation",
            "input_fingerprint",
            "policy_version",
            "prompt_version",
            "schema_version",
            "model_revision",
            "input_snapshot",
            "generation",
            "status",
            "condition",
            "sufficient",
            "reason",
            "inference_refs",
            "media_references",
            "result",
            "created_at",
            "updated_at",
            "analyzed_at",
            "publication_order",
        ),
    ),
    "runtime.assessmenthead": (
        AssessmentHead,
        (
            "observation",
            "input_fingerprint",
            "generation",
            "current",
            "confirmed",
            "updated_at",
        ),
    ),
}
