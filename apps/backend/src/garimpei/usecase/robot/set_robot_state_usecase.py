from garimpei.domain.robot.control import RobotCommand
from garimpei.domain.robot.ports import RobotControlRepository


class SetRobotStateUseCase:
    def __init__(self, repository: RobotControlRepository) -> None:
        self._repository = repository

    def execute(self, command: RobotCommand) -> None:
        self._repository.command(command)
