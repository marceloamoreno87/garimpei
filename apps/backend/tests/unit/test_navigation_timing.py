from dataclasses import replace
from uuid import uuid4

from garimpei.domain.listing.ports import Attempt
from garimpei.domain.navigation.catalog import Catalog
from garimpei.domain.navigation.policy import NavigationPolicy
from garimpei.usecase.navigation.run_slice_usecase import RunSliceUseCase
from garimpei.usecase.navigation.run_suggestions_usecase import RunSuggestionsUseCase
from tests.factories.navigation_timing import (
    CollectionStoreFake,
    MonotonicClockFake,
    SuggestionStoreFake,
    TimedNavigationSource,
    TurnQueueFake,
    timing_scope,
    timing_suggestion,
    timing_unit,
)


def test_rebuild_two_operations_does_not_start_with_only_40_seconds_left() -> None:
    clock, scope = MonotonicClockFake(), timing_scope()
    store = TurnQueueFake([timing_unit(scope, cursor="source:opaque")], clock)
    source = TimedNavigationSource(clock)
    runner = RunSliceUseCase(
        CollectionStoreFake(scope, clock, 80),
        store,
        source,
        source,
        Catalog("1", (), ()),
        NavigationPolicy(),
        clock.now,
        20,
        1.2,
    )
    runner.execute(Attempt(uuid4(), 1))
    assert "search" not in source.calls
    assert clock.now() <= 120 and store.yielded


def test_database_delay_cannot_start_an_operation_after_admission_expires() -> None:
    clock, scope = MonotonicClockFake(), timing_scope()
    store = TurnQueueFake([timing_unit(scope)], clock, claim_delay=110)
    source = TimedNavigationSource(clock)
    RunSliceUseCase(
        CollectionStoreFake(scope, clock),
        store,
        source,
        source,
        Catalog("1", (), ()),
        NavigationPolicy(),
        clock.now,
        20,
        1.2,
    ).execute(Attempt(uuid4(), 1))
    assert "search" not in source.calls and clock.now() <= 120


def test_geocoding_does_not_start_when_its_timeout_cannot_fit() -> None:
    clock, scope = MonotonicClockFake(), timing_scope()
    store = TurnQueueFake([timing_unit(scope)], clock)
    source = TimedNavigationSource(clock)
    RunSliceUseCase(
        CollectionStoreFake(scope, clock, 119),
        store,
        source,
        source,
        Catalog("1", (), ()),
        NavigationPolicy(),
        clock.now,
        20,
        1.2,
    ).execute(Attempt(uuid4(), 1))
    assert source.calls == []


def test_active_120_seconds_and_first_tenth_detail_boundaries() -> None:
    scope = timing_scope()
    for duration, seconds, expected in [(21.2, 120, 5), (1, 1200, 10)]:
        clock = MonotonicClockFake()
        store = TurnQueueFake(
            [timing_unit(scope, index, detail=True) for index in range(20)]
            + [timing_unit(scope, 99)],
            clock,
        )
        source = TimedNavigationSource(clock, detail_seconds=duration)
        policy = replace(NavigationPolicy(), slice_seconds=seconds)
        RunSliceUseCase(
            CollectionStoreFake(scope, clock),
            store,
            source,
            source,
            Catalog("1", (), ()),
            policy,
            clock.now,
            20,
            1.2,
        ).execute(Attempt(uuid4(), 1))
        assert source.calls.count("detail") == expected
        assert "search" not in source.calls and clock.now() <= seconds


def test_suggestion_claim_delay_cannot_spend_more_than_45_seconds() -> None:
    clock, scope = MonotonicClockFake(), timing_scope()
    store = SuggestionStoreFake(timing_suggestion(scope), clock, claim_delay=30)
    source = TimedNavigationSource(clock)
    RunSuggestionsUseCase(store, source, NavigationPolicy(), clock.now, 20, 1.2).execute()
    assert source.calls == [] and clock.now() <= 45


def test_suggestions_at_exact_45_seconds_and_no_detail_when_it_cannot_fit() -> None:
    scope = timing_scope()
    for search_duration, confirmed in [(23.8, True), (23.8001, False)]:
        clock = MonotonicClockFake()
        store = SuggestionStoreFake(timing_suggestion(scope), clock)
        source = TimedNavigationSource(clock, search_seconds=search_duration)
        RunSuggestionsUseCase(store, source, NavigationPolicy(), clock.now, 20, 1.2).execute()
        assert store.confirmed is confirmed
        assert clock.now() <= 45 and source.calls.count("search") == 1
        assert source.calls.count("detail") == int(confirmed)
