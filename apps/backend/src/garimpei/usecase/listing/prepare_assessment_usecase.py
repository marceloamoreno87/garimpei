from uuid import UUID

from garimpei.domain.listing.assessment_ports import (
    AssessmentInference,
    AssessmentInputs,
    AssessmentRepository,
    AssessmentWork,
    Clock,
)


class PrepareAssessmentUseCase:
    def __init__(
        self,
        inputs: AssessmentInputs,
        repository: AssessmentRepository,
        inference: AssessmentInference,
        clock: Clock,
    ) -> None:
        self._inputs, self._repository, self._inference, self._clock = (
            inputs,
            repository,
            inference,
            clock,
        )

    def execute(self, identity: UUID) -> AssessmentWork:
        work = self._repository.prepare(self._inputs.read(identity), self._clock())
        if not work.requests or not work.pins:
            requests, pins = self._inference.submit(work)
            self._repository.attach(work, requests, pins, self._clock())
        return self._repository.work(work.id)
