from garimpei.domain.listing.listing import Candidate, Evidence
from garimpei.domain.listing.ports import (
    Attempt,
    CollectionStore,
    Geocoding,
    ListingSource,
    ListingUnavailable,
    SourceFailure,
    SupersededAttempt,
)
from garimpei.domain.listing.scope import Scope
from garimpei.domain.navigation.catalog import Catalog
from garimpei.domain.navigation.policy import NavigationPolicy
from garimpei.domain.navigation.ports import Monotonic, NavigationStore
from garimpei.domain.navigation.work import NavigationUnit
from garimpei.domain.robot.admission import admitted_unit
from garimpei.domain.robot.errors import RobotPaused, RobotUnavailable
from garimpei.domain.robot.ports import RobotAdmission


class RunSliceUseCase:
    def __init__(
        self,
        collection: CollectionStore,
        navigation: NavigationStore,
        source: ListingSource,
        geocoding: Geocoding,
        catalog: Catalog,
        policy: NavigationPolicy,
        monotonic: Monotonic,
        timeout: int,
        cadence: float,
        robot: RobotAdmission | None = None,
    ) -> None:
        self._robot = robot
        self._collection, self._navigation, self._source = collection, navigation, source
        self._geocoding, self._catalog, self._policy = geocoding, catalog, policy
        self._monotonic, self._timeout, self._cadence = monotonic, timeout, cadence

    def execute(self, attempt: Attempt) -> None:
        try:
            self._run(attempt)
        except (SupersededAttempt, RobotPaused, RobotUnavailable):
            return

    def _run(self, attempt: Attempt) -> None:
        started, pages, details = self._monotonic(), 0, 0
        work = self._collection.begin(attempt)
        scope = self._catalog.decorate_scope(work.scope)
        self._navigation.prepare(attempt, scope)
        if not self._can_start(started):
            self._navigation.yield_slice(attempt, scope)
            return
        try:
            with admitted_unit(
                self._robot,
                "navigation_context",
                scope.key,
                str(scope.revision),
                attempt.generation,
            ):
                self._collection.set_origin(attempt, self._geocoding.resolve(scope.cep))
        except (RobotPaused, RobotUnavailable):
            self._navigation.yield_slice(attempt, scope)
            return
        except SourceFailure:
            self._collection.set_origin(attempt, None)
        while self._can_start(started):
            if pages >= self._policy.slice_pages or details >= self._policy.slice_details:
                break
            unit = self._navigation.claim(
                attempt,
                scope,
                pages=self._policy.slice_pages - pages,
                details=details < self._policy.slice_details,
            )
            if unit is None:
                break
            cost = 2 if unit.cursor and unit.cursor.startswith("source:") else 1
            if not self._can_start(started, cost):
                break
            used_pages, used_details, stop = self._step(attempt, scope, unit)
            pages += used_pages
            details += used_details
            if stop:
                break
        self._navigation.yield_slice(attempt, scope)

    def _can_start(self, started: float, operations: int = 1) -> bool:
        return (
            self._monotonic() - started + operations * (self._timeout + self._cadence)
            <= self._policy.slice_seconds
        )

    def _step(self, attempt: Attempt, scope: Scope, unit: NavigationUnit) -> tuple[int, int, bool]:
        try:
            with admitted_unit(
                self._robot, "navigation", unit.unit_key, str(unit.revision), unit.generation
            ):
                return self._step_authorized(attempt, scope, unit)
        except (RobotPaused, RobotUnavailable):
            return 0, 0, True

    def _step_authorized(
        self, attempt: Attempt, scope: Scope, unit: NavigationUnit
    ) -> tuple[int, int, bool]:
        try:
            if unit.target is None:
                page = self._source.search(scope, unit.search, unit.cursor)
                self._navigation.page(attempt, unit, page)
                return page.traversed_pages, 0, False
            self._navigation.detail(attempt, unit, self._detail(scope, unit))
            return 0, 1, False
        except SourceFailure as failure:
            stop = self._navigation.failed(attempt, unit, failure)
            return (1, 0, stop) if unit.target is None else (0, 1, stop)

    def _detail(self, scope: Scope, unit: NavigationUnit) -> Candidate:
        assert unit.target is not None
        try:
            return self._source.detail(scope, unit.target.external_id)
        except ListingUnavailable as unavailable:
            if unavailable.external_id != unit.target.external_id or not unit.target.known:
                raise SourceFailure("unverified_new_listing_unavailable") from None
            return Candidate(
                unit.target.external_id,
                Evidence(source_available=False, availability_evidence=unavailable.evidence),
                "detail",
            )
