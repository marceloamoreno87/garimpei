from uuid import UUID

from garimpei.domain.listing.assessment_ports import (
    AssessmentInference,
    AssessmentInputs,
    AssessmentRepository,
    AssessmentWork,
    Clock,
)
from garimpei.domain.robot.admission import admitted_unit
from garimpei.domain.robot.ports import RobotAdmission


class PrepareAssessmentUseCase:
    def __init__(
        self,
        inputs: AssessmentInputs,
        repository: AssessmentRepository,
        inference: AssessmentInference,
        clock: Clock,
        robot: RobotAdmission | None = None,
    ) -> None:
        self._robot = robot
        self._inputs, self._repository, self._inference, self._clock = (
            inputs,
            repository,
            inference,
            clock,
        )

    def execute(self, identity: UUID) -> AssessmentWork:
        with admitted_unit(self._robot, "assessment", str(identity)):
            return self._prepare(identity)

    def _prepare(self, identity: UUID) -> AssessmentWork:
        work = self._repository.prepare(self._inputs.read(identity), self._clock())
        if not work.requests or not work.pins:
            requests, pins = self._inference.submit(work)
            self._repository.attach(work, requests, pins, self._clock())
        return self._repository.work(work.id)
