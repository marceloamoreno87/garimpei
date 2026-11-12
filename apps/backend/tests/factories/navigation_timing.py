from dataclasses import dataclass, replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

from garimpei.domain.listing.geography import Point
from garimpei.domain.listing.listing import Candidate, Evidence, Match
from garimpei.domain.listing.ports import (
    Attempt,
    CollectionPolicy,
    Page,
    Revisit,
    SourceFailure,
    Work,
)
from garimpei.domain.listing.scope import Scope, Search
from garimpei.domain.navigation.work import NavigationUnit, SuggestionUnit, Turn


@dataclass
class MonotonicClockFake:
    seconds: float = 0

    def now(self) -> float:
        return self.seconds

    def advance(self, seconds: float) -> None:
        self.seconds += seconds


class CollectionStoreFake:
    def __init__(self, scope: Scope, clock: MonotonicClockFake, delay: float = 0) -> None:
        self.scope, self.clock, self.delay = scope, clock, delay

    def begin(self, attempt: Attempt) -> Work:
        self.clock.advance(self.delay)
        return Work(self.scope, frozenset(), False)

    def set_origin(self, attempt: Attempt, point: Point | None) -> None:
        pass

    def reconcile(self, policy: CollectionPolicy) -> None:
        raise AssertionError("Unexpected collection reconciliation")

    def stage(self, attempt: Attempt, key: str, candidates: tuple[Candidate, ...]) -> None:
        raise AssertionError("Publication belongs to navigation transaction")

    def record(
        self,
        attempt: Attempt,
        key: str,
        failure: SourceFailure | None,
        window_proof: str | None = None,
    ) -> None:
        raise AssertionError("Publication belongs to navigation transaction")

    def detail_targets(
        self, attempt: Attempt, *, include_known: bool = True
    ) -> tuple[Revisit, ...]:
        raise AssertionError("Targets belong to navigation transaction")

    def mark_scanned(self, attempt: Attempt, point: Point | None) -> None:
        raise AssertionError("Completion belongs to navigation transaction")

    def publish_batch(self, attempt: Attempt, *, ready_only: bool = False) -> bool:
        raise AssertionError("Publication belongs to navigation transaction")

    def finish(self, attempt: Attempt, policy: CollectionPolicy) -> None:
        raise AssertionError("Completion belongs to navigation transaction")


class TurnQueueFake:
    def __init__(
        self, units: list[NavigationUnit], clock: MonotonicClockFake, claim_delay: float = 0
    ) -> None:
        self.units, self.clock, self.claim_delay = units, clock, claim_delay
        self.confirmed: list[str] = []
        self.yielded = False

    def prepare(self, attempt: Attempt, scope: Scope) -> None:
        pass

    def claim(
        self, attempt: Attempt, scope: Scope, *, pages: int, details: bool
    ) -> NavigationUnit | None:
        self.clock.advance(self.claim_delay)
        return self.units.pop(0) if self.units else None

    def page(self, attempt: Attempt, unit: NavigationUnit, page: Page) -> None:
        self.confirmed.append(unit.unit_key)

    def detail(self, attempt: Attempt, unit: NavigationUnit, candidate: Candidate) -> None:
        self.confirmed.append(unit.unit_key)

    def failed(self, attempt: Attempt, unit: NavigationUnit, failure: SourceFailure) -> bool:
        return failure.access or failure.retry_after > 0

    def yield_slice(self, attempt: Attempt, scope: Scope) -> None:
        self.yielded = True

    def resume(self, identity: UUID, revision: int) -> None:
        raise AssertionError("No resume command during a slice")

    def request_research(
        self,
        request_id: UUID,
        revision: int,
        interest: str,
        term: str,
        purpose: str,
        constraints: str,
    ) -> UUID:
        raise AssertionError("No research command during a slice")


class TimedNavigationSource:
    def __init__(
        self, clock: MonotonicClockFake, search_seconds: float = 21.2, detail_seconds: float = 21.2
    ) -> None:
        self.clock, self.search_seconds, self.detail_seconds = clock, search_seconds, detail_seconds
        self.calls: list[str] = []

    def resolve(self, cep: str) -> Point | None:
        self.calls.append("geocoding")
        return None

    def search(self, scope: Scope, query: Search, continuation: str | None) -> Page:
        self.calls.append("search")
        cost = 2 if continuation and continuation.startswith("source:") else 1
        self.clock.advance(cost * self.search_seconds)
        return Page(
            (Candidate("1304", Evidence(title=query.term), "card", (query.interest,)),),
            None,
            traversed_pages=cost,
        )

    def detail(self, scope: Scope, external_id: str) -> Candidate:
        self.calls.append("detail")
        self.clock.advance(self.detail_seconds)
        return Candidate(external_id, Evidence(title="PS5 Pro"), "detail")


class SuggestionStoreFake:
    def __init__(
        self, unit: SuggestionUnit, clock: MonotonicClockFake, claim_delay: float = 0
    ) -> None:
        self.unit, self.clock, self.claim_delay = unit, clock, claim_delay
        self.confirmed = False
        self.failures: list[str] = []

    def claim(self) -> SuggestionUnit:
        self.clock.advance(self.claim_delay)
        return self.unit

    def page(self, unit: SuggestionUnit, page: Page) -> str | None:
        return page.candidates[0].external_id if page.candidates else None

    def confirm(self, unit: SuggestionUnit, candidate: Candidate) -> None:
        self.confirmed = True

    def failed(self, unit: SuggestionUnit, failure: SourceFailure) -> None:
        self.failures.append(failure.reason)


def timing_scope() -> Scope:
    return Scope(
        uuid4(),
        "facebook_marketplace",
        "01001000",
        2,
        "scope",
        (Search(Match("product", "ps5 slim"), "PS5 Slim", "marketplace"),),
    )


def timing_unit(
    scope: Scope, index: int = 0, *, detail: bool = False, cursor: str | None = None
) -> NavigationUnit:
    query = scope.searches[0]
    target = Revisit(str(1300 + index), (query.interest,)) if detail else None
    return NavigationUnit(
        Turn(uuid4(), query.key, "investigation" if detail else "discovery", index, None),
        index + 1,
        scope.revision,
        query,
        (query.term,),
        0,
        cursor,
        (),
        0,
        0,
        0,
        target,
        "detail:" + str(index) if detail else "page:" + str(index),
    )


def timing_suggestion(scope: Scope) -> SuggestionUnit:
    return SuggestionUnit(
        uuid4(),
        scope,
        replace(scope.searches[0], term="PS5 Pro"),
        "slim-pro",
        datetime(2026, 1, 1, tzinfo=UTC),
        "",
    )


@dataclass
class UtcClockFake:
    value: datetime

    def now(self) -> datetime:
        return self.value

    def advance(self, seconds: int) -> None:
        from datetime import timedelta

        self.value += timedelta(seconds=seconds)
