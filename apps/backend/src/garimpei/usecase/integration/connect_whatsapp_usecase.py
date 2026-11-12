from garimpei.domain.integration.ports import SessionGateway


class ConnectWhatsAppUseCase:
    def __init__(self, gateway: SessionGateway, session: str) -> None:
        self._gateway, self._session = gateway, session

    def execute(self) -> None:
        self._gateway.connect(self._session)
