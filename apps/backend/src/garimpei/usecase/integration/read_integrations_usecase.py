from garimpei.domain.integration.ports import IntegrationRepository, SessionGateway
from garimpei.domain.integration.values import Group, IntegrationUnavailable, IntegrationView


class ReadIntegrationsUseCase:
    def __init__(
        self, repository: IntegrationRepository, gateway: SessionGateway, session: str
    ) -> None:
        self._repository, self._gateway, self._session = repository, gateway, session

    def execute(self, *, groups: bool = True) -> IntegrationView:
        config = self._repository.read()
        state = self._gateway.state(config.whatsapp_session or self._session)
        choices: tuple[Group, ...] = ()
        unavailable = False
        if groups and state.phase == "WORKING":
            try:
                choices = self._gateway.groups(config.whatsapp_session or self._session)
            except IntegrationUnavailable:
                unavailable = True
        return IntegrationView(config, state, choices, unavailable)
