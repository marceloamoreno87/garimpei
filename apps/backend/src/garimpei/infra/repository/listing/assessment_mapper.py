from dataclasses import asdict
from datetime import datetime
from typing import cast
from uuid import UUID

from garimpei.domain.listing.assessment import Assessment, Finding, Reference
from garimpei.domain.listing.assessment_ports import AssessmentInput, AssessmentWork
from garimpei.infra.persistence.assessment_models import ConditionAssessment


def encode_assessment(value: Assessment) -> dict[str, object]:
    return asdict(value)


def decode_assessment(raw: dict[str, object]) -> Assessment:
    return Assessment(
        UUID(str(raw["id"])) if raw.get("id") else None,
        UUID(str(raw["observation_id"])) if raw.get("observation_id") else None,
        str(raw.get("fingerprint", "")),
        str(raw.get("policy_version", "condition-policy-v1")),
        str(raw.get("status", "waiting")),
        str(raw.get("reason", "waiting_inference")),
        str(raw.get("condition", "uncertain")),
        raw.get("sufficient") is True,
        str(raw.get("model_revision", "")),
        datetime.fromisoformat(str(raw["analyzed_at"])) if raw.get("analyzed_at") else None,
        tuple(
            Finding(
                str(f["dimension"]),
                str(f["assessment"]),
                str(f["description"]),
                tuple(
                    Reference(**cast(dict[str, str], r))
                    for r in cast(list[dict[str, object]], f["references"])
                ),
            )
            for f in cast(list[dict[str, object]], raw.get("findings", []))
        ),
        tuple(cast(list[str], raw.get("limitations", []))),
        tuple(cast(list[dict[str, object]], raw.get("photo_coverage", []))),
        UUID(str(raw["previous"])) if raw.get("previous") else None,
        int(str(raw.get("revision", 0))),
    )


def work_from_row(row: ConditionAssessment) -> AssessmentWork:
    return AssessmentWork(
        row.id,
        row.generation,
        AssessmentInput(
            row.listing_id,
            row.observation_id,
            row.observation.ordinal,
            row.input_fingerprint,
            row.model_revision,
            row.input_snapshot,
        ),
        tuple(UUID(str(r)) for r in row.inference_refs),
        tuple(UUID(str(r)) for r in row.media_references),
    )
