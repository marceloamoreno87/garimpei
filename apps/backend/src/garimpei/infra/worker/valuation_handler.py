import logging
from collections.abc import Callable
from uuid import UUID

from garimpei.domain.robot.errors import RobotPaused, RobotUnavailable
from garimpei.domain.valuation.ports import Clock, ValuationStore
from garimpei.usecase.valuation.evaluate_usecase import EvaluateValuationUseCase

logger = logging.getLogger(__name__)


class ValuationTaskHandler:
    def __init__(
        self,
        evaluate: EvaluateValuationUseCase,
        store: ValuationStore,
        clock: Clock,
        on_pause: Callable[[UUID], None] | None = None,
    ) -> None:
        self._evaluate, self._store, self._clock = evaluate, store, clock
        self._on_pause = on_pause

    def execute(self, identity: UUID) -> None:
        try:
            self._evaluate.execute(identity)
        except (RobotPaused, RobotUnavailable):
            if self._on_pause is not None:
                self._on_pause(identity)
            return
        except Exception:
            self._store.failed(identity, self._clock())
            logger.exception(
                "valuation_publication_failed",
                extra={"event": "valuation_publication_failed", "valuation_work": str(identity)},
            )
