from garimpei.domain.integration.ports import SessionGateway
from garimpei.domain.integration.values import IntegrationError


class ReadWhatsAppQrUseCase:
    def __init__(self, gateway: SessionGateway, session: str) -> None:
        self._gateway, self._session = gateway, session

    def execute(self) -> bytes:
        if self._gateway.state(self._session).phase != "SCAN_QR_CODE":
            raise IntegrationError("O QR não está disponível. Atualize o estado da conexão.")
        return self._gateway.qr(self._session)
