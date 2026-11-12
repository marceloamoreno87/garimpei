from garimpei.domain.integration.ports import IntegrationRepository
from garimpei.domain.integration.values import FacebookSession
from garimpei.domain.valuation.ports import Clock


class SaveFacebookSessionUseCase:
    def __init__(self, repository: IntegrationRepository, clock: Clock) -> None:
        self._repository, self._clock = repository, clock

    def execute(self, raw: str) -> None:
        self._repository.save_facebook(FacebookSession.parse(raw, self._clock()))
