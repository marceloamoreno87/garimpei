from dataclasses import replace
from datetime import datetime
from uuid import UUID

from garimpei.domain.valuation.identity import identify
from garimpei.domain.valuation.policy import NEW_WINDOW
from garimpei.domain.valuation.values import NewReference, Resale, Valuation
from garimpei.infra.persistence.listing_models import CollectionState, Listing
from garimpei.infra.persistence.valuation_models import ValuationEvaluation, ValuationProgress
from garimpei.infra.repository.valuation.mapper import decode_valuation, mapping
from garimpei.infra.repository.valuation.postgres_repository import _listing


class PostgresValuationQueries:
    def current(self, identity: UUID, now: datetime) -> Valuation | None:
        listing = Listing.objects.select_related("latest").filter(id=identity).first()
        if listing is None or listing.latest is None:
            return None
        progress = (
            ValuationProgress.objects.select_related("current").filter(listing_id=identity).first()
        )
        return self._value(listing, progress, now, self._diagnostic())

    def current_many(self, listings: tuple[Listing, ...], now: datetime) -> dict[UUID, Valuation]:
        progress = {
            p.listing_id: p
            for p in ValuationProgress.objects.select_related("current").filter(
                listing_id__in=[row.id for row in listings]
            )
        }
        diagnostic = self._diagnostic()
        return {row.id: self._value(row, progress.get(row.id), now, diagnostic) for row in listings}

    @staticmethod
    def _diagnostic() -> str | None:
        return (
            "falha_de_origem" if CollectionState.objects.filter(failures__gt=0).exists() else None
        )

    @staticmethod
    def _value(
        listing: Listing, progress: ValuationProgress | None, now: datetime, diagnostic: str | None
    ) -> Valuation:
        identity = listing.id
        target = _listing(listing)
        if progress is None or progress.current is None:
            return Valuation(
                None,
                identity,
                0,
                target.revision,
                identify(target.evidence),
                now,
                Resale(None, "aguardando_avaliacao", (), 0, 0, None),
                NewReference("aguardando_avaliacao"),
            )
        value = decode_valuation(mapping(progress.current.result))
        if identify(target.evidence) != value.product:
            return replace(
                value,
                resale=replace(value.resale, price=None, reason="aguardando_avaliacao"),
                new=NewReference("aguardando_avaliacao"),
            )
        if value.resale.valid_until is not None and now > value.resale.valid_until:
            value = replace(
                value, resale=replace(value.resale, price=None, reason="evidencia_vencida")
            )
        if value.new.quote is not None and now > value.new.quote.observed_at + NEW_WINDOW:
            value = replace(
                value,
                new=NewReference(
                    "fonte_indisponivel" if value.new.diagnostic else "referencia_vencida",
                    diagnostic=value.new.diagnostic,
                ),
            )
        return replace(value, origin_diagnostic=diagnostic)

    def historical(self, identity: UUID) -> Valuation | None:
        row = ValuationEvaluation.objects.filter(id=identity).first()
        return decode_valuation(mapping(row.result)) if row else None
