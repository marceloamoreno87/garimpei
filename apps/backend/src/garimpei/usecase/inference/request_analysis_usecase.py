from garimpei.domain.inference.ports import AnalysisTicket, InferenceRepository, InputPreparer
from garimpei.domain.inference.request import AnalysisInput


class RequestAnalysisUseCase:
    def __init__(self, repository: InferenceRepository, preparer: InputPreparer) -> None:
        self._repository, self._preparer = repository, preparer

    def execute(self, value: AnalysisInput) -> AnalysisTicket:
        artifact = self._preparer.artifact()
        return self._repository.admit(value, artifact, self._preparer.prepare(value))
