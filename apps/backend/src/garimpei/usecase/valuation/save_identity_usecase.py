from garimpei.domain.valuation.identity_ports import IdentityEdit, IdentityRepository, IdentityView


class SaveIdentityUseCase:
    def __init__(self, repository: IdentityRepository) -> None:
        self._repository = repository

    def execute(self, command: IdentityEdit) -> IdentityView:
        return self._repository.save(command)
