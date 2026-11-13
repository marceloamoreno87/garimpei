from dataclasses import replace

from garimpei.domain.listing.ports import ListingSource, SourceFailure
from garimpei.domain.navigation.policy import NavigationPolicy
from garimpei.domain.navigation.ports import Monotonic, SuggestionStore
from garimpei.domain.navigation.work import SuggestionUnit
from garimpei.domain.robot.admission import admitted_unit
from garimpei.domain.robot.errors import RobotPaused, RobotUnavailable
from garimpei.domain.robot.ports import RobotAdmission


class RunSuggestionsUseCase:
    def __init__(
        self,
        store: SuggestionStore,
        source: ListingSource,
        policy: NavigationPolicy,
        monotonic: Monotonic,
        timeout: int,
        cadence: float,
        robot: RobotAdmission | None = None,
    ) -> None:
        self._robot = robot
        self._store, self._source, self._policy = store, source, policy
        self._monotonic, self._timeout, self._cadence = monotonic, timeout, cadence

    def execute(self) -> None:
        started = self._monotonic()
        unit = self._store.claim()
        if unit is None:
            return
        if (
            self._monotonic() - started + self._timeout + self._cadence
            > self._policy.suggestion_seconds
        ):
            self._store.failed(unit, SourceFailure("suggestion_budget_exhausted"))
            return
        try:
            identity = unit.pending_id
            if not identity:
                identity = self._search(unit)
            if (
                identity
                and self._monotonic() - started + self._timeout + self._cadence
                <= self._policy.suggestion_seconds
            ):
                self._detail(unit, identity)
        except (RobotPaused, RobotUnavailable):
            return
        except SourceFailure as failure:
            self._store.failed(unit, failure)

    def _search(self, unit: SuggestionUnit) -> str:
        with admitted_unit(self._robot, "suggestion", str(unit.id), str(unit.scope.revision)):
            page = self._source.search(unit.scope, unit.query, None)
            return self._store.page(unit, page) or ""

    def _detail(self, unit: SuggestionUnit, identity: str) -> None:
        with admitted_unit(self._robot, "suggestion", str(unit.id), str(unit.scope.revision)):
            self._store.confirm(
                replace(unit, pending_id=identity), self._source.detail(unit.scope, identity)
            )
