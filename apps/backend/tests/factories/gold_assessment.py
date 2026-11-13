"""F15 fake transport with actual bounded F19 image artifacts for backup/recovery tests."""

import hashlib
from dataclasses import replace

from django.utils.timezone import now

from garimpei.config.env import load_inference_settings
from garimpei.domain.inference.ports import PreparedPart
from garimpei.domain.inference.request import AnalysisInput
from garimpei.infra.gateway.inference.input_preparer import image_derivative
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
from tests.factories.assessment import (
    AssessmentContext,
    ControlledConditionGateway,
    ControlledConditionPreparer,
)


class GoldConditionPreparer(ControlledConditionPreparer):
    def prepare(self, value: AnalysisInput) -> tuple[PreparedPart, ...]:
        settings = load_inference_settings()
        parts = super().prepare(value)
        prepared = []
        for part in parts:
            assert part.image_hash is not None
            source = settings.directory / "sources" / part.image_hash
            data = image_derivative(source.read_bytes())
            digest = hashlib.sha256(data).hexdigest()
            (settings.directory / digest).write_bytes(data)
            prepared.append(replace(part, image_hash=digest))
        return tuple(prepared)


def gold_assessment_context() -> AssessmentContext:
    repository = PostgresAssessmentRepository()
    gateway = ControlledConditionGateway()
    inference_repository = PostgresInferenceRepository(lambda: 0, 100)
    inference = LocalAssessmentInference(
        RequestAnalysisUseCase(inference_repository, GoldConditionPreparer()),
        build_media_repository(),
        build_media_store(),
        PostgresMediaQueries(),
    )
    return AssessmentContext(
        PrepareAssessmentUseCase(LocalAssessmentInputs(), repository, inference, now),
        CompleteAssessmentUseCase(repository, inference, now),
        RunAnalysisUseCase(inference_repository, gateway, now),
        gateway,
        repository,
    )
