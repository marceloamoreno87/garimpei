"""Named deterministic inference fakes. They do not measure GPU or model quality."""

import json
from dataclasses import dataclass
from threading import Event
from typing import TYPE_CHECKING

from garimpei.domain.inference.condition_evidence import VERSION
from garimpei.domain.inference.errors import InferenceError
from garimpei.domain.inference.ports import PreparedPart
from garimpei.domain.inference.request import AnalysisInput

if TYPE_CHECKING:
    from garimpei.infra.repository.listing.assessment_repository import PostgresAssessmentRepository
    from garimpei.usecase.inference.run_analysis_usecase import RunAnalysisUseCase
    from garimpei.usecase.listing.complete_assessment_usecase import CompleteAssessmentUseCase
    from garimpei.usecase.listing.prepare_assessment_usecase import PrepareAssessmentUseCase


class ControlledConditionPreparer:
    def artifact(self) -> str:
        from garimpei.config.env import load_inference_settings
        from garimpei.infra.gateway.inference.input_preparer import artifact_signature, read_lock

        return artifact_signature(read_lock(load_inference_settings().model_lock))

    def prepare(self, value: AnalysisInput) -> tuple[PreparedPart, ...]:
        from garimpei.config.env import load_inference_settings
        from garimpei.infra.gateway.inference.input_preparer import read_lock
        from garimpei.infra.gateway.inference.registry import registered

        parts = []
        for image in value.images:
            meta = registered(load_inference_settings(), image.id)
            parts.append(
                PreparedPart(
                    "image-" + image.id,
                    value.text,
                    image.id,
                    image.sha256,
                    (
                        dict(
                            kind="image",
                            id=image.id,
                            sha256=image.sha256,
                            source_sha256=meta["source_sha256"],
                        ),
                    ),
                    model_digest=str(
                        read_lock(load_inference_settings().model_lock)["model_digest"]
                    ),
                    profile=VERSION,
                )
            )
        return tuple(parts)


class ControlledConditionGateway:
    kind = "light_wear"
    calls = 0
    fault: str | None = None
    held: Event
    release: Event

    def __init__(self) -> None:
        self.held, self.release = Event(), Event()
        self.release.set()

    def infer(self, part: PreparedPart, artifact: str) -> dict[str, object]:
        self.calls += 1
        self.held.set()
        if not self.release.wait(20):
            raise InferenceError("timeout")
        if self.fault:
            raise InferenceError(self.fault)
        findings = []
        examined = []
        if part.image_id:
            original = part.coverage[0]["source_sha256"]
            findings = [
                dict(
                    dimension="appearance",
                    assessment=self.kind,
                    description="Sinal visual do controle sintético",
                    references=[dict(kind="image", photo_id=part.image_id, sha256=original)],
                )
            ]
            examined = [dict(photo_id=part.image_id, sha256=original)]
        result = dict(
            schema_version=VERSION,
            findings=findings,
            conflicts=[],
            limitations=["Bateria e portas precisam de teste presencial"],
            examined_photos=examined,
            omitted_photos=[],
        )
        return dict(content=json.dumps(result), metrics=dict(controlled_fake=True))

    def diagnose(self) -> dict[str, object]:
        return dict(service=True, resident=False, reason="controlled_fixture")

    def unload(self) -> bool:
        return True

    def recover(self) -> bool:
        return True


@dataclass
class AssessmentContext:
    prepare: "PrepareAssessmentUseCase"
    complete: "CompleteAssessmentUseCase"
    run: "RunAnalysisUseCase"
    gateway: ControlledConditionGateway
    repository: "PostgresAssessmentRepository"


def assessment_context() -> AssessmentContext:
    from django.utils.timezone import now

    from garimpei.infra.gateway.listing.assessment_inference import LocalAssessmentInference
    from garimpei.infra.gateway.listing.assessment_inputs import LocalAssessmentInputs
    from garimpei.infra.queries.media.postgres_queries import PostgresMediaQueries
    from garimpei.infra.repository.inference.postgres_repository import PostgresInferenceRepository
    from garimpei.infra.repository.listing.assessment_repository import PostgresAssessmentRepository
    from garimpei.main import build_media_repository, build_media_store
    from garimpei.usecase.inference.request_analysis_usecase import RequestAnalysisUseCase
    from garimpei.usecase.inference.run_analysis_usecase import RunAnalysisUseCase
    from garimpei.usecase.listing.complete_assessment_usecase import CompleteAssessmentUseCase
    from garimpei.usecase.listing.prepare_assessment_usecase import PrepareAssessmentUseCase

    repository = PostgresAssessmentRepository()
    gateway = ControlledConditionGateway()
    irepo = PostgresInferenceRepository(lambda: 0, 100)
    request = RequestAnalysisUseCase(irepo, ControlledConditionPreparer())
    inference = LocalAssessmentInference(
        request, build_media_repository(), build_media_store(), PostgresMediaQueries()
    )
    return AssessmentContext(
        PrepareAssessmentUseCase(LocalAssessmentInputs(), repository, inference, now),
        CompleteAssessmentUseCase(repository, inference, now),
        RunAnalysisUseCase(irepo, gateway, now),
        gateway,
        repository,
    )
