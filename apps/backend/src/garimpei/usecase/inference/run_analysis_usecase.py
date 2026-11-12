from typing import cast

from garimpei.domain.inference.errors import InferenceError
from garimpei.domain.inference.ports import Clock, InferenceGateway, InferenceRepository
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
        received = False
        try:
            envelope = self._gateway.infer(work.part, work.artifact)
            received = True
            raw = envelope.get("content")
            if not isinstance(raw, str):
                raise InferenceError("invalid_output")
            images = (work.part.image_id,) if work.part.image_id is not None else ()
            result = validate_result(raw, work.part.text, images)
            payload: dict[str, object] = {
                "findings": list(result.findings),
                "unknowns": list(result.unknowns),
                "limitations": list(result.limitations),
            }
            metrics = cast(dict[str, object], envelope.get("metrics", {}))
            return self._repository.publish(work, payload, metrics, self._clock())
        except InferenceError as error:
            self._repository.failed(work, error.code, self._clock(), sent=received or error.sent)
            return False
