from uuid import UUID

from django.db import DatabaseError

from garimpei.domain.inference.errors import InferenceError
from garimpei.domain.inference.ports import InferenceStatus
from garimpei.domain.inference.request import MODEL
from garimpei.infra.persistence.inference_models import (
    InferenceControl,
    InferencePart,
    InferenceRequest,
)
from garimpei.infra.repository.inference.postgres_repository import _current


class PostgresInferenceQueries:
    def analysis(self, identity: UUID) -> dict[str, object]:
        row = InferenceRequest.objects.filter(pk=identity).first()
        if row is None:
            raise InferenceError("analysis_not_found", 404)
        parts = list(InferencePart.objects.filter(request=row).order_by("position"))
        coverage = [
            dict(
                entry,
                sent=part.metrics.get("sent") is True,
                examined=part.state == "succeeded",
                reason="examined" if part.state == "succeeded" else part.reason or part.state,
            )
            for part in parts
            for entry in part.content["coverage"]
        ]
        return {
            "request_id": str(row.id),
            "observation_id": str(row.observation_id) if row.observation_id else None,
            "target_kind": row.target_kind,
            "target_id": str(row.target_id) if row.target_id else None,
            "target_revision": row.target_revision,
            "revision": row.revision,
            "state": row.state if _current(row) else "superseded",
            "model": MODEL,
            "artifact": row.artifact,
            "model_digest": parts[0].content.get("model_digest", "") if parts else "",
            "prompt_version": row.prompt_version,
            "schema_version": row.schema_version,
            "cohort_id": str(row.cohort_id) if row.cohort_id else None,
            "cohort_generation": row.cohort_generation,
            "coverage": coverage,
            "parts": [
                {
                    "state": part.state,
                    "result": part.result,
                    "metrics": part.metrics,
                    "reason": part.reason,
                }
                for part in parts
            ],
            "created_at": row.created_at.isoformat(),
            "completed_at": row.completed_at.isoformat() if row.completed_at else None,
        }

    def status(self) -> InferenceStatus:
        try:
            control, _ = InferenceControl.objects.get_or_create(pk=1)
            queued = InferenceRequest.objects.filter(
                state__in=["pending", "awaiting_resource", "paused"]
            ).count()
            last = (
                InferenceRequest.objects.filter(state="succeeded").order_by("-completed_at").first()
            )
            reason = control.reason
            if (
                reason == "execution_unknown"
                and control.active_request is not None
                and InferenceRequest.objects.filter(
                    pk=control.active_request, reason="timeout"
                ).exists()
            ):
                reason = "timeout"
            return InferenceStatus(
                control.revision,
                control.paused,
                control.active_request is not None,
                queued,
                control.resident,
                reason,
                control.checked_at,
                MODEL,
                control.artifact,
                control.service,
                last.completed_at if last else None,
            )
        except DatabaseError:
            raise InferenceError("read_failed", 503) from None
