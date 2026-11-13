from typing import cast

from garimpei.domain.inference.condition_evidence import (
    VERSION as CONDITION_VERSION,
)
from garimpei.domain.inference.condition_evidence import (
    validate_condition_result,
)
from garimpei.domain.inference.errors import InferenceError
from garimpei.domain.inference.ports import Clock, InferenceGateway, InferenceRepository
from garimpei.domain.inference.request import SUPPORTED_PROFILES
from garimpei.domain.inference.result import validate_result


class RunAnalysisUseCase:
    def __init__(
        self, repository: InferenceRepository, gateway: InferenceGateway, clock: Clock
    ) -> None:
        self._repository, self._gateway, self._clock = repository, gateway, clock

    def execute(self) -> bool:
        work = self._repository.claim(self._clock())
        if work is None:
            return False
        if not self._repository.authorize(work):
            return False
        if work.part.profile not in SUPPORTED_PROFILES:
            self._repository.failed(
                work,
                "unsupported_prompt_or_schema",
                self._clock(),
                diagnostic="unsupported_profile",
            )
            return False
        received = False
        metrics: dict[str, object] = {}
        try:
            envelope = self._gateway.infer(work.part, work.artifact)
            received = True
            metrics = cast(dict[str, object], envelope.get("metrics", {}))
            raw = envelope.get("content")
            if not isinstance(raw, str):
                raise InferenceError("invalid_output")
            images = (work.part.image_id,) if work.part.image_id is not None else ()
            if work.part.profile == CONDITION_VERSION:
                photos = (
                    {
                        work.part.image_id: str(
                            work.part.coverage[0].get(
                                "source_sha256", work.part.coverage[0]["sha256"]
                            )
                        )
                    }
                    if work.part.image_id
                    else {}
                )
                condition_payload = validate_condition_result(raw, work.part.text, photos)
                return self._repository.publish(work, condition_payload, metrics, self._clock())
            result = validate_result(raw, work.part.text, images)
            payload: dict[str, object] = {
                "findings": list(result.findings),
                "unknowns": list(result.unknowns),
                "limitations": list(result.limitations),
            }
            return self._repository.publish(work, payload, metrics, self._clock())
        except InferenceError as error:
            self._repository.failed(
                work,
                error.code,
                self._clock(),
                sent=received or error.sent,
                diagnostic=error.diagnostic or ("result_validation_failed" if received else ""),
                metrics=metrics | error.metrics,
            )
            return False
