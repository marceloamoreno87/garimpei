from garimpei.domain.robot.control import RobotStatus
from garimpei.domain.robot.ports import RobotQueries


class ReadRobotStatusUseCase:
    def __init__(self, queries: RobotQueries) -> None:
        self._queries = queries

    def execute(self) -> RobotStatus:
        return self._queries.status()
