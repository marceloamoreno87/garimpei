from collections.abc import Mapping
from dataclasses import replace
from datetime import datetime
from uuid import UUID

from garimpei.domain.valuation.policy import NEW_WINDOW
from garimpei.domain.valuation.values import NewReference, Resale, Valuation
from garimpei.infra.persistence.identity_models import IdentityProgress
from garimpei.infra.persistence.listing_models import CollectionState, Listing
from garimpei.infra.persistence.valuation_models import ValuationEvaluation, ValuationProgress
from garimpei.infra.repository.valuation.identity_mapper import identify_row
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
        identity_progress = (
            IdentityProgress.objects.select_related("manual__observation")
            .filter(listing=listing)
            .first()
        )
        return self._value(listing, progress, now, self._diagnostic(), identity_progress)

    def current_many(
        self,
        listings: tuple[Listing, ...],
        now: datetime,
        *,
        identities: Mapping[UUID, IdentityProgress | None] | None = None,
    ) -> dict[UUID, Valuation]:
        progress = {
            p.listing_id: p
            for p in ValuationProgress.objects.select_related("current").filter(
                listing_id__in=[row.id for row in listings]
            )
        }
        diagnostic = self._diagnostic()
        # Snapshot callers already load this provenance with their listings.
        if identities is None:
            identities = {
                p.listing_id: p
                for p in IdentityProgress.objects.select_related("manual__observation").filter(
                    listing_id__in=[row.id for row in listings]
                )
            }
        return {
            row.id: self._value(row, progress.get(row.id), now, diagnostic, identities.get(row.id))
            for row in listings
        }

    @staticmethod
    def _diagnostic() -> str | None:
        return (
            "falha_de_origem" if CollectionState.objects.filter(failures__gt=0).exists() else None
        )

    @staticmethod
    def _value(
        listing: Listing,
        progress: ValuationProgress | None,
        now: datetime,
        diagnostic: str | None,
        progress_identity: IdentityProgress | None = None,
    ) -> Valuation:
        identity = listing.id
        identity_view = identify_row(listing, progress_identity)
        target = _listing(listing, identity_view)
        if identity_view.state != "identified":
            return Valuation(
                None,
                identity,
                0,
                target.revision,
                None,
                now,
                Resale(None, identity_view.reason, (), 0, 0, None),
                NewReference(identity_view.reason or "produto_indeterminado"),
                identification=identity_view,
            )
        if (
            progress is None
            or progress.current is None
            or (identity_view.manual_revision and not progress.signature)
        ):
            return Valuation(
                None,
                identity,
                0,
                target.revision,
                target.product,
                now,
                Resale(None, "aguardando_avaliacao", (), 0, 0, None),
                NewReference("aguardando_avaliacao"),
                identification=identity_view,
            )
        value = replace(
            decode_valuation(mapping(progress.current.result)), identification=identity_view
        )
        if target.product != value.product:
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
        return replace(value, origin_diagnostic=diagnostic, identification=identity_view)

    def historical(self, identity: UUID) -> Valuation | None:
        row = ValuationEvaluation.objects.filter(id=identity).first()
        return decode_valuation(mapping(row.result)) if row else None
