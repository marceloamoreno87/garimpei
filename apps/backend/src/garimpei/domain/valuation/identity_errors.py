class IdentityError(Exception):
    code = "IDENTITY_UNAVAILABLE"
    status = 503
    message = "Não foi possível consultar ou gravar a identidade. Tente novamente."

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.message
        super().__init__(self.message)


class InvalidIdentityInput(IdentityError):
    code = "INVALID_IDENTITY_INPUT"
    status = 400
    message = "Identidade inválida: confira ação, revisões e atributos esperados."


class InvalidIdentityCombination(IdentityError):
    code = "INVALID_IDENTITY_COMBINATION"
    status = 422
    message = "Modelo e atributos não formam uma identidade suportada. Revise os valores."


class IdentityConflict(IdentityError):
    code = "IDENTITY_REVISION_CONFLICT"
    status = 409
    message = "A observação ou a correção mudou. Reabra os detalhes antes de salvar."


class IdentityNotFound(IdentityError):
    code = "IDENTITY_NOT_FOUND"
    status = 404
    message = "Anúncio ausente: escolha um anúncio existente antes de corrigir."
