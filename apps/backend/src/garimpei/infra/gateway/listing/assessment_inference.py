import json
from dataclasses import replace
from typing import cast
from uuid import UUID

from django.utils.timezone import now

from garimpei.config.env import load_inference_settings
from garimpei.domain.inference.condition_evidence import VERSION
from garimpei.domain.inference.request import AnalysisInput
from garimpei.domain.listing.assessment import Assessment, Finding, Reference
from garimpei.domain.listing.assessment_policy import decide
from garimpei.domain.listing.assessment_ports import AssessmentWork
from garimpei.domain.listing.listing import Evidence
from garimpei.domain.media.ports import MediaQueries, MediaRepository, MediaStore
from garimpei.domain.robot.admission import admitted_unit
from garimpei.domain.robot.ports import RobotAdmission
from garimpei.infra.gateway.listing.assessment_media import prepare_photos
from garimpei.infra.persistence.assessment_models import ConditionAssessment
from garimpei.infra.queries.inference.postgres_queries import PostgresInferenceQueries
from garimpei.infra.repository.listing.assessment_mapper import decode_assessment
from garimpei.usecase.inference.request_analysis_usecase import RequestAnalysisUseCase


class LocalAssessmentInference:
    def __init__(
        self,
        request: RequestAnalysisUseCase,
        media: MediaRepository,
        store: MediaStore,
        queries: MediaQueries,
        robot: RobotAdmission | None = None,
    ) -> None:
        self._robot = robot
        self._request, self._media, self._store, self._queries = request, media, store, queries

    def submit(self, work: AssessmentWork) -> tuple[tuple[UUID, ...], tuple[UUID, ...]]:
        row = ConditionAssessment.objects.get(id=work.id)
        if row.publication_order is not None:
            return work.requests, work.pins
        references, pins, omissions = prepare_photos(
            work, self._media, self._store, self._queries, load_inference_settings(), self._robot
        )
        if omissions:
            row.input_snapshot = dict(row.input_snapshot, technical_omissions=omissions)
            row.save(update_fields=["input_snapshot"])
        if work.requests or row.reason == "cached_result":
            return work.requests, pins
        if not references:
            return (), pins
        refs = list(references)
        requests = []
        context = json.dumps(
            {key: work.value.snapshot[key] for key in ["text", "category", "identity"]},
            ensure_ascii=False,
            sort_keys=True,
        )
        # Original source hashes must remain the public evidence identity even though F19 registers a derivative.
        for index in range(0, len(refs), 4):
            value = AnalysisInput(
                work.value.observation_id,
                work.value.observation_revision,
                context,
                tuple(refs[index : index + 4]),
                VERSION,
                VERSION,
                work.id,
                work.generation,
            )
            with admitted_unit(
                self._robot, "assessment_part", str(work.id), str(index), work.generation
            ):
                ticket = self._request.execute(value)
                requests.append(ticket.request_id)
        return tuple(requests), pins

    def result(self, work: AssessmentWork) -> Assessment | None:
        row = ConditionAssessment.objects.get(id=work.id)
        if row.publication_order is not None:
            return None
        if row.reason == "cached_result" and row.result:
            return replace(
                decode_assessment(row.result),
                id=work.id,
                observation_id=work.value.observation_id,
                previous=None,
                photo_coverage=tuple(
                    dict(p, examined=True, reason="reused_confirmed_content")
                    for p in cast(list[dict[str, object]], work.value.snapshot["photos"])
                ),
            )
        snapshot = work.value.snapshot
        photos = cast(list[dict[str, object]], snapshot["photos"])
        if not work.requests:
            reason = (
                "partial_photo_coverage"
                if snapshot.get("technical_omissions")
                else "no_photos"
                if snapshot["presence"] == "none"
                else "waiting_photos"
            )
            return self._resolved(work, (), False, reason, analyzed=False)
        responses = [PostgresInferenceQueries().analysis(r) for r in work.requests]
        if any(
            r["state"] in {"pending", "running", "awaiting_resource", "paused"} for r in responses
        ):
            return None
        if any(r["state"] == "superseded" for r in responses):
            return self._resolved(work, (), False, "superseded_input", status="failed")
        failed = next(
            (
                str(part["reason"] or part["state"])
                for r in responses
                for part in cast(list[dict[str, object]], r["parts"])
                if part["state"] != "succeeded"
            ),
            None,
        )
        if failed:
            return self._resolved(work, (), False, _failure(failed), status="failed")
        if any(
            not isinstance(p["result"], dict)
            for r in responses
            for p in cast(list[dict[str, object]], r["parts"])
        ):
            return self._resolved(work, (), False, "invalid_analysis", status="failed")
        if any(not _matches_request(response, work) for response in responses):
            return self._resolved(work, (), False, "invalid_analysis", status="failed")
        findings: list[Finding] = []
        limitations = []
        examined: set[str] = set()
        conflicts = False
        for response in responses:
            for part in cast(list[dict[str, object]], response["parts"]):
                result = cast(dict[str, object], part["result"])
                findings.extend(_findings(result))
                limitations.extend(cast(list[str], result["limitations"]))
                examined.update(
                    str(p["photo_id"])
                    for p in cast(list[dict[str, str]], result["examined_photos"])
                )
                conflicts = conflicts or bool(result["conflicts"])
        expected = {str(p["photo_id"]) for p in photos}
        complete = (
            snapshot["complete"] is True
            and expected == examined
            and all(p["state"] == "available" for p in photos)
        )
        return self._resolved(
            work,
            tuple(findings),
            complete,
            "partial_photo_coverage",
            limitations=tuple(limitations),
            conflicts=conflicts,
            examined=examined,
            controlled=any(
                cast(dict[str, object], p["metrics"]).get("controlled_fake") is True
                for r in responses
                for p in cast(list[dict[str, object]], r["parts"])
            ),
        )

    @staticmethod
    def _resolved(
        work: AssessmentWork,
        findings: tuple[Finding, ...],
        complete: bool,
        reason: str,
        *,
        status: str = "complete",
        limitations: tuple[str, ...] = (),
        conflicts: bool = False,
        examined: set[str] | None = None,
        controlled: bool = False,
        analyzed: bool = True,
    ) -> Assessment:
        snapshot = work.value.snapshot
        fields = cast(dict[str, str | None], snapshot["text"])
        decision = decide(
            Evidence(
                title=fields.get("title"),
                description=fields.get("description"),
                condition=fields.get("condition"),
            ),
            str(snapshot["category"]),
            findings,
            complete=complete,
            reason=reason,
            conflicts=conflicts,
        )
        omissions = cast(dict[str, str], snapshot.get("technical_omissions", {}))
        limitations = limitations + tuple(
            "Foto " + identity + ": " + code for identity, code in omissions.items()
        )
        coverage = tuple(
            dict(
                p,
                examined=str(p["photo_id"]) in (examined or set()),
                reason="examined"
                if str(p["photo_id"]) in (examined or set())
                else omissions.get(str(p["sha256"]), reason),
            )
            for p in cast(list[dict[str, object]], snapshot["photos"])
        )
        return Assessment(
            id=work.id,
            observation_id=work.value.observation_id,
            fingerprint=work.value.fingerprint,
            status=status if complete or status == "failed" else "partial",
            # A missing seller declaration must not hide a rejected model response.
            reason=reason if status == "failed" else decision.reason,
            condition=decision.condition,
            sufficient=decision.sufficient,
            model_revision=work.value.model_revision,
            analyzed_at=now() if analyzed else None,
            findings=findings,
            limitations=limitations,
            photo_coverage=coverage,
            runtime="controlled_fake" if controlled else "local_model",
        )


def _findings(value: dict[str, object]) -> tuple[Finding, ...]:
    return tuple(
        Finding(
            str(f["dimension"]),
            str(f["assessment"]),
            str(f["description"]),
            tuple(
                Reference(**cast(dict[str, str], r))
                for r in cast(list[dict[str, object]], f["references"])
            ),
        )
        for f in cast(list[dict[str, object]], value["findings"])
    )


def _failure(code: str) -> str:
    return {
        "timeout": "inference_timeout",
        "out_of_memory": "gpu_resource_unavailable",
        "gpu_unavailable": "gpu_resource_unavailable",
        "invalid_output": "invalid_analysis",
        "superseded": "superseded_input",
    }.get(code, "model_unavailable")


def _matches_request(response: dict[str, object], work: AssessmentWork) -> bool:
    return bool(
        response.get("observation_id") == str(work.value.observation_id)
        and response.get("revision") == work.value.observation_revision
        and response.get("model_digest") == work.value.model_revision
        and response.get("prompt_version") == VERSION
        and response.get("schema_version") == VERSION
        and response.get("cohort_id") == str(work.id)
        and response.get("cohort_generation") == work.generation
    )
