from uuid import UUID

from garimpei.domain.listing.assessment_ports import (
    AssessmentInference,
    AssessmentRepository,
    Clock,
)


class CompleteAssessmentUseCase:
    def __init__(
        self, repository: AssessmentRepository, inference: AssessmentInference, clock: Clock
    ) -> None:
        self._repository, self._inference, self._clock = repository, inference, clock

    def execute(self, identity: UUID) -> bool:
        work = self._repository.work(identity)
        result = self._inference.result(work)
        return self._repository.publish(work, result, self._clock()) if result else False
