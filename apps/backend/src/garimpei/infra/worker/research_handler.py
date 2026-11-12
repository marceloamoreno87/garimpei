from collections.abc import Callable

from garimpei.usecase.valuation.run_research_usecase import RunComparableResearchUseCase


class ComparableResearchTaskHandler:
    def __init__(
        self, research: RunComparableResearchUseCase, close: Callable[[], None] | None = None
    ) -> None:
        self._research, self._close = research, close

    def execute(self) -> None:
        try:
            self._research.execute()
        finally:
            if self._close is not None:
                self._close()
