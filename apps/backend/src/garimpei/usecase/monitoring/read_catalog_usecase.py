from garimpei.domain.monitoring.errors import CatalogUnavailable
from garimpei.domain.monitoring.ports import CatalogGateway
from garimpei.domain.monitoring.values import CategoryCatalog


class ReadCategoryCatalogUseCase:
    def __init__(self, gateway: CatalogGateway) -> None:
        self._gateway = gateway

    def execute(self) -> CategoryCatalog | None:
        try:
            return self._gateway.load()
        except CatalogUnavailable:
            # Browsing/editing products remains possible while the category adapter is unavailable.
            return None
