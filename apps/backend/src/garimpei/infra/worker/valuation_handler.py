import logging
from uuid import UUID

from garimpei.domain.valuation.ports import Clock, ValuationStore
from garimpei.usecase.valuation.evaluate_usecase import EvaluateValuationUseCase

logger = logging.getLogger(__name__)


class ValuationTaskHandler:
    def __init__(
        self, evaluate: EvaluateValuationUseCase, store: ValuationStore, clock: Clock
    ) -> None:
        self._evaluate, self._store, self._clock = evaluate, store, clock

    def execute(self, identity: UUID) -> None:
        try:
            self._evaluate.execute(identity)
        except Exception:
            self._store.failed(identity, self._clock())
            logger.exception(
                "valuation_publication_failed",
                extra={"event": "valuation_publication_failed", "valuation_work": str(identity)},
            )
