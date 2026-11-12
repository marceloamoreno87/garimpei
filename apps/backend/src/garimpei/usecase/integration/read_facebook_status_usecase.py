from garimpei.domain.integration.ports import IntegrationRepository
from garimpei.domain.integration.values import IntegrationConfiguration


class ReadFacebookStatusUseCase:
    def __init__(self, repository: IntegrationRepository) -> None:
        self._repository = repository

    def execute(self) -> IntegrationConfiguration:
        return self._repository.read()
