from collections.abc import Callable

from garimpei.domain.listing.listing import Candidate, Evidence
from garimpei.domain.listing.ports import (
    ListingSource,
    ListingUnavailable,
    SourceFailure,
    SupersededAttempt,
)
from garimpei.domain.robot.admission import admitted_unit
from garimpei.domain.robot.errors import RobotPaused, RobotUnavailable
from garimpei.domain.robot.ports import RobotAdmission
from garimpei.domain.valuation.research import ResearchStore, ResearchUnit


class RunComparableResearchUseCase:
    def __init__(
        self,
        store: ResearchStore,
        source: ListingSource,
        monotonic: Callable[[], float],
        source_overhead_seconds: float = 0,
        robot: RobotAdmission | None = None,
        on_pause: Callable[[ResearchUnit], None] | None = None,
    ) -> None:
        self._robot, self._on_pause = robot, on_pause
        self._store, self._source, self._monotonic = store, source, monotonic
        self._source_overhead = source_overhead_seconds

    def execute(self) -> None:
        unit = self._store.claim()
        if unit is None:
            return
        try:
            self._run(unit)
        except (RobotPaused, RobotUnavailable):
            if self._on_pause is not None:
                self._on_pause(unit)
            else:
                self._store.yield_slice(unit)
        except SupersededAttempt:
            return

    def _run(self, unit: ResearchUnit) -> None:
        started, pages, details = self._monotonic(), 0, 0
        current: ResearchUnit | None = unit
        while current is not None and self._can_start(current, started, pages, details):
            current, used_pages, used_details = self._step(current)
            pages, details = pages + used_pages, details + used_details
        if current:
            self._store.yield_slice(current)

    def _can_start(self, unit: ResearchUnit, started: float, pages: int, details: int) -> bool:
        cost = 1 if unit.pending else 2 if unit.cursor else 1
        # A cold native resume can geocode, acquire/open the profile, rebuild and continue.
        # Reserve those bounded calls before I/O rather than budgeting only the final page.
        calls = 3 if unit.pending else 6 if unit.cursor else 5
        if (
            self._monotonic()
            - started
            + calls * (unit.limits.request_timeout_seconds + self._source_overhead)
            > unit.limits.max_slice_seconds
        ):
            return False
        if unit.pending:
            return details < unit.limits.max_details_per_slice
        return (
            pages + cost <= unit.limits.max_queries_per_slice
            and unit.pages + cost <= unit.limits.max_pages_per_query
        )

    def _step(self, unit: ResearchUnit) -> tuple[ResearchUnit | None, int, int]:
        with admitted_unit(
            self._robot, "research", str(unit.id), str(unit.scope.revision), unit.generation
        ):
            return self._step_authorized(unit)

    def _step_authorized(self, unit: ResearchUnit) -> tuple[ResearchUnit | None, int, int]:
        try:
            if unit.pending:
                candidate = self._source.detail(unit.scope, unit.pending[0])
                return self._store.detail(unit, candidate), 0, 1
            page = self._source.search(unit.scope, unit.query, unit.cursor)
            return self._store.page(unit, page), page.traversed_pages, 0
        except ListingUnavailable as unavailable:
            if not unit.pending or unavailable.external_id != unit.pending[0]:
                self._store.failed(unit, SourceFailure("unverified_identity"))
                return None, 0, 0
            candidate = Candidate(
                unavailable.external_id,
                Evidence(source_available=False, availability_evidence=unavailable.evidence),
                "detail",
            )
            return self._store.detail(unit, candidate), 0, 1
        except SourceFailure as failure:
            self._store.failed(unit, failure)
        return None, 0, 0
