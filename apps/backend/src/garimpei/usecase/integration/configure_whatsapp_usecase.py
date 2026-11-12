from garimpei.domain.integration.ports import IntegrationRepository, SessionGateway
from garimpei.domain.integration.values import Group, IntegrationError, group_id


class ConfigureWhatsAppUseCase:
    def __init__(
        self, repository: IntegrationRepository, gateway: SessionGateway, session: str
    ) -> None:
        self._repository, self._gateway, self._session = repository, gateway, session

    def execute(self, identity: str, expected_account: str, enabled: bool) -> None:
        before = self._gateway.state(self._session)
        if before.phase != "WORKING" or not before.account or before.account != expected_account:
            raise IntegrationError(
                "A conexão do WhatsApp mudou. Atualize a página e conecte novamente."
            )
        choices = self._gateway.groups(self._session)
        selected = next((group for group in choices if group.id == identity), None)
        if selected is None or not group_id(identity):
            raise IntegrationError("Selecione um grupo disponível nesta conta do WhatsApp.")
        after = self._gateway.state(self._session)
        if after != before:
            raise IntegrationError(
                "A conta mudou durante a gravação. Atualize a página e tente novamente."
            )
        self._repository.configure_whatsapp(
            self._session, before.account, Group(selected.id, selected.name), enabled
        )
