from __future__ import annotations

from dataclasses import replace
from typing import cast
from uuid import UUID

from django.db import DatabaseError, connection, transaction
from django.db.models import F, Q, QuerySet

from garimpei.domain.listing.condition import Choice
from garimpei.domain.listing.exploration import (
    Criteria,
    ExpiredExploration,
    ExplorationError,
    Offer,
    OfferPage,
)
from garimpei.infra.persistence.exploration_models import ExplorationOffer, ExplorationRevision
from garimpei.infra.persistence.listing_models import Listing, ManualCondition
from garimpei.infra.queries.listing.exploration_mapper import decode
from garimpei.infra.queries.listing.identity_overlay import identity_overlay


class PostgresExplorationQueries:
    def page(self, criteria: Criteria) -> OfferPage:
        try:
            with transaction.atomic():
                self._isolation()
                return self._page(criteria)
        except DatabaseError:
            raise ExplorationError() from None

    @staticmethod
    def _isolation() -> None:
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")

    @staticmethod
    def _revision(version: UUID | None) -> ExplorationRevision | None:
        if version is None:
            return ExplorationRevision.objects.order_by("-sequence").first()
        revision = ExplorationRevision.objects.filter(id=version).first()
        if revision is None:
            raise ExpiredExploration()
        return revision

    def _page(self, criteria: Criteria) -> OfferPage:
        revision = self._revision(criteria.version)
        if revision is None:
            return OfferPage(criteria, (), 0, 1, (0, 0, 0), None)
        rows = self._rows(revision).filter(visible=True)
        counts = tuple(
            rows.filter(self._tab(tab)).count() for tab in ("funcionam", "defeitos", "incerta")
        )
        filtered = rows.filter(self._tab(criteria.tab), search__contains=criteria.search)
        if criteria.category:
            filtered = filtered.filter(categories__contains=[criteria.category])
        total = filtered.count()
        pages = max(1, (total + 19) // 20)
        page = min(criteria.page, pages)
        ordered = filtered.order_by(
            F("profit").desc(nulls_last=True), "-first_seen_at", "listing_id"
        )[(page - 1) * 20 : page * 20]
        offers = tuple(self._decode(row, revision) for row in ordered)
        return OfferPage(
            criteria.at(revision.id, page),
            offers,
            total,
            pages,
            counts,
            revision.published_at,
        )

    @staticmethod
    def _tab(tab: str) -> Q:
        automatic = Q(listing__manual_condition__isnull=True, automatic_tab=tab)
        if tab == "incerta":
            return automatic
        return automatic | Q(
            listing__manual_condition__choice="good" if tab == "funcionam" else "defect"
        )

    @staticmethod
    def _rows(revision: ExplorationRevision) -> QuerySet[ExplorationOffer]:
        return ExplorationOffer.objects.filter(revision=revision).select_related(
            "listing__manual_condition",
            "listing__latest",
            "listing__identity_progress__manual__observation",
        )

    @staticmethod
    def _decode(row: ExplorationOffer, revision: ExplorationRevision) -> Offer:
        from garimpei.infra.queries.media.postgres_queries import availability_overlay

        offer = decode(row.payload, revision.published_at)
        offer = replace(offer, media=availability_overlay(offer.media))
        manual: ManualCondition | None = getattr(row.listing, "manual_condition", None)
        if manual:
            offer = replace(
                offer,
                condition=replace(
                    offer.condition, manual=cast(Choice, manual.choice), revision=manual.revision
                ),
            )
        return identity_overlay(offer, row.listing)

    def detail(self, identity: UUID, version: UUID | None) -> tuple[Offer | None, UUID | None]:
        try:
            with transaction.atomic():
                self._isolation()
                return self._detail(identity, version)
        except DatabaseError:
            raise ExplorationError() from None

    def _detail(self, identity: UUID, version: UUID | None) -> tuple[Offer | None, UUID | None]:
        if not Listing.objects.filter(id=identity).exists():
            return None, version
        revision = self._revision(version)
        if revision is None:
            return None, version
        row: ExplorationOffer | None = self._rows(revision).filter(listing_id=identity).first()
        if row is None:
            row = (
                ExplorationOffer.objects.select_related(
                    "revision",
                    "listing__manual_condition",
                    "listing__latest",
                    "listing__identity_progress__manual__observation",
                )
                .filter(listing_id=identity)
                .order_by("-revision_id")
                .first()
            )
        return (self._decode(row, row.revision), revision.id) if row else (None, revision.id)

    def updates(self, version: UUID | None) -> tuple[bool, bool]:
        try:
            latest = ExplorationRevision.objects.order_by("-sequence").first()
            expired = (
                version is not None and not ExplorationRevision.objects.filter(id=version).exists()
            )
            return bool(latest and latest.id != version), expired
        except DatabaseError:
            raise ExplorationError() from None
