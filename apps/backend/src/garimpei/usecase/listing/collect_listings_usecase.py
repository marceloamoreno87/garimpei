from dataclasses import replace

from garimpei.domain.listing.listing import Candidate, Evidence
from garimpei.domain.listing.ports import (
    Attempt,
    CollectionPolicy,
    CollectionStore,
    Geocoding,
    ListingSource,
    ListingUnavailable,
    Revisit,
    SourceFailure,
    SupersededAttempt,
    Work,
)
from garimpei.domain.listing.scope import Scope, Search


class CollectListingsUseCase:
    def __init__(
        self,
        store: CollectionStore,
        source: ListingSource,
        geocoding: Geocoding,
        policy: CollectionPolicy,
    ) -> None:
        self._store = store
        self._source = source
        self._geocoding = geocoding
        self._policy = policy

    def execute(self, attempt: Attempt) -> None:
        try:
            work = self._store.begin(attempt)
            if not work.scanned:
                self._scan(attempt, work)
            while self._store.publish_batch(attempt):
                pass
            self._store.finish(attempt, self._policy)
        except SupersededAttempt:
            return
        except SourceFailure:
            self._finish_interrupted(attempt)

    def _finish_interrupted(self, attempt: Attempt) -> None:
        try:
            self._publish_ready(attempt)
            self._store.finish(attempt, self._policy)
        except SupersededAttempt:
            return

    def _scan(self, attempt: Attempt, work: Work) -> None:
        self._store.reset_unit(attempt, "geocoding")
        try:
            point = self._geocoding.resolve(work.scope.cep)
        except SourceFailure as failure:
            self._store.record(attempt, "geocoding", failure)
            point = None
        self._store.set_origin(attempt, point)
        for query in work.scope.searches:
            if query.key not in work.results:
                self._search(attempt, work.scope, query)
            self._enrich(attempt, work.scope, include_known=False)
        self._enrich(attempt, work.scope, include_known=True)
        self._store.mark_scanned(attempt, point)

    def _enrich(self, attempt: Attempt, scope: Scope, *, include_known: bool) -> None:
        failures = 0
        for index, target in enumerate(
            self._store.detail_targets(attempt, include_known=include_known)
        ):
            successful = self._detail(attempt, scope, f"detail:{target.external_id}", target)
            failures = 0 if successful else failures + 1
            if failures >= 3:
                failure = SourceFailure("detail_failures_pause", self._policy.retry_base)
                self._store.record(attempt, "source_health", failure)
                raise failure
            if (index + 1) % 10 == 0:
                self._publish_ready(attempt)
        self._publish_ready(attempt)

    def _publish_ready(self, attempt: Attempt) -> None:
        while self._store.publish_batch(attempt, ready_only=True):
            pass

    def _search(self, attempt: Attempt, scope: Scope, query: Search) -> None:
        key = query.key
        self._store.reset_unit(attempt, key)
        try:
            proof = self._pages(attempt, scope, query)
        except SourceFailure as failure:
            self._store.record(attempt, key, failure)
            if failure.access or failure.retry_after > 0:
                raise
        else:
            self._store.record(attempt, key, None, proof)

    def _pages(self, attempt: Attempt, scope: Scope, query: Search) -> str:
        continuation = None
        visited: set[str] = set()
        page_identities: set[tuple[str, ...]] = set()
        invalid = 0
        diagnostic = None
        for _ in range(self._policy.max_pages):
            page = self._source.search(scope, query, continuation)
            identities = tuple(sorted({candidate.external_id for candidate in page.candidates}))
            if identities and identities in page_identities:
                raise SourceFailure("repeated_page")
            page_identities.add(identities)
            candidates = tuple(
                candidate
                for candidate in page.candidates
                if scope.window is None
                or scope.window.contains(candidate.evidence.published_at) is not False
            )
            self._store.stage(attempt, query.key, candidates)
            self._enrich(attempt, scope, include_known=False)
            invalid += page.invalid_cards
            diagnostic = page.diagnostic or diagnostic
            continuation = page.continuation
            if continuation is None and diagnostic:
                raise SourceFailure(diagnostic)
            if continuation is None and invalid:
                raise SourceFailure("unverified_identity")
            if continuation is None:
                return page.window_proof or "source_exhausted"
            if continuation in visited:
                raise SourceFailure("repeated_continuation")
            visited.add(continuation)
        raise SourceFailure("window_limit")

    def _detail(self, attempt: Attempt, scope: Scope, key: str, target: Revisit) -> bool:
        self._store.reset_unit(attempt, key)
        try:
            candidate = self._source.detail(scope, target.external_id)
        except ListingUnavailable as unavailable:
            if unavailable.external_id != target.external_id or not target.known:
                self._store.record(
                    attempt, key, SourceFailure("unverified_new_listing_unavailable")
                )
                return False
            candidate = Candidate(
                target.external_id,
                Evidence(
                    source_available=False,
                    availability_evidence=unavailable.evidence,
                ),
                "detail",
            )
        except SourceFailure as failure:
            self._store.record(attempt, key, failure)
            if failure.access or failure.retry_after > 0:
                raise
            return False
        self._store.stage(attempt, key, (replace(candidate, matches=target.matches),))
        self._store.record(attempt, key, None)
        return True
