class MonitoringError(Exception):
    code = "INVALID_CONFIGURATION"
    status = 422

    def __init__(self, message: str, field: str = "interests") -> None:
        super().__init__(message)
        self.field = field


class ConfigurationConflict(MonitoringError):
    code = "CONFIGURATION_CONFLICT"
    status = 409

    def __init__(self) -> None:
        super().__init__(
            "Existe uma alteração mais recente. Recarregue antes de salvar.", "revision"
        )


class CatalogUnavailable(MonitoringError):
    code = "CATEGORY_CATALOG_UNAVAILABLE"
    status = 503

    def __init__(self) -> None:
        super().__init__(
            "Categorias indisponíveis. Recarregue para tentar novamente.", "category_ids"
        )


class ConfigurationSaveFailed(MonitoringError):
    code = "CONFIGURATION_SAVE_FAILED"
    status = 503

    def __init__(self) -> None:
        super().__init__("Não foi possível confirmar a gravação. Tente novamente.", "save")


class ConfigurationReadFailed(MonitoringError):
    code = "CONFIGURATION_READ_FAILED"
    status = 503

    def __init__(self) -> None:
        super().__init__("Não foi possível consultar a configuração. Tente novamente.", "read")
