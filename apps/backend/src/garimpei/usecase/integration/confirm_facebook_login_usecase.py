from garimpei.domain.integration.facebook_login import FacebookLoginRepository


class ConfirmFacebookLoginUseCase:
    def __init__(self, repository: FacebookLoginRepository) -> None:
        self._repository = repository

    def execute(self) -> None:
        self._repository.confirm_login()
