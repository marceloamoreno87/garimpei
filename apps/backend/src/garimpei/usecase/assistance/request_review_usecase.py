from garimpei.domain.assistance.ports import AssistanceRepository
from garimpei.domain.assistance.review import ReviewCommand, ReviewTicket


class RequestReviewUseCase:
    def __init__(self, repository: AssistanceRepository) -> None:
        self._repository = repository

    def execute(self, command: ReviewCommand) -> ReviewTicket:
        return self._repository.admit(command)
