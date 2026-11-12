from garimpei.domain.inference.ports import InferenceRepository


class PauseInferenceUseCase:
    def __init__(self, repository: InferenceRepository) -> None:
        self._repository = repository

    def execute(self, revision: int) -> None:
        self._repository.control(True, revision)
