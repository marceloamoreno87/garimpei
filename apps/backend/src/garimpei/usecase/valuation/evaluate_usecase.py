from datetime import datetime, timedelta
from uuid import UUID, uuid4

from garimpei.domain.valuation.identity import identify
from garimpei.domain.valuation.policy import NEW_WINDOW, USED_WINDOW, estimate, new_reference
from garimpei.domain.valuation.ports import Clock, NewPriceSource, NewSourceFailure, ValuationStore
from garimpei.domain.valuation.values import NewQuote, NewReference, Valuation


class EvaluateValuationUseCase:
    def __init__(self, store: ValuationStore, source: NewPriceSource, clock: Clock) -> None:
        self._store, self._source, self._clock = store, source, clock

    def execute(self, identity: UUID) -> None:
        work = self._store.work(identity)
        if work is None:
            return
        now = self._clock()
        product = identify(work.target.evidence)
        reference = NewReference("produto_indeterminado")
        if product is not None:
            reference = self._reference(product, work.previous, now)
        resale = estimate(work.target, work.candidates, now)
        value = Valuation(
            uuid4(),
            work.listing_id,
            work.revision,
            work.target.revision,
            product,
            now,
            resale,
            reference,
        )
        due = now + NEW_WINDOW
        expirations = [
            row.observed_at + USED_WINDOW
            for row in work.candidates
            if row.observed_at + USED_WINDOW >= now
        ]
        if reference.quote:
            expirations.append(reference.quote.observed_at + NEW_WINDOW)
        if expirations:
            due = min(due, min(expirations)) + timedelta(microseconds=1)
        if reference.failures:
            backoff = (60, 300, 900, 3600)[min(reference.failures - 1, 3)]
            due = min(due, now + timedelta(seconds=backoff))
        self._store.publish(work, value, due)

    def _reference(
        self, product: str, previous: NewReference | None, now: datetime
    ) -> NewReference:
        failed = False
        offers: tuple[NewQuote, ...] = ()
        try:
            offers = self._source.offers(product, now)
        except NewSourceFailure:
            failed = True
        result = new_reference(product, offers, failed, previous.quote if previous else None, now)
        return NewReference(
            result.state,
            result.quote,
            result.diagnostic,
            (previous.failures if previous else 0) + 1 if failed else 0,
        )
