from dataclasses import replace

from garimpei.domain.listing.ports import ListingSource, SourceFailure
from garimpei.domain.navigation.policy import NavigationPolicy
from garimpei.domain.navigation.ports import Monotonic, SuggestionStore


class RunSuggestionsUseCase:
    def __init__(
        self,
        store: SuggestionStore,
        source: ListingSource,
        policy: NavigationPolicy,
        monotonic: Monotonic,
        timeout: int,
        cadence: float,
    ) -> None:
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
                page = self._source.search(unit.scope, unit.query, None)
                identity = self._store.page(unit, page) or ""
            if (
                identity
                and self._monotonic() - started + self._timeout + self._cadence
                <= self._policy.suggestion_seconds
            ):
                self._store.confirm(
                    replace(unit, pending_id=identity), self._source.detail(unit.scope, identity)
                )
        except SourceFailure as failure:
            self._store.failed(unit, failure)
