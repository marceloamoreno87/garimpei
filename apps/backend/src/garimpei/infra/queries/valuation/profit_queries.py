import logging
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from django.db import DatabaseError, connection, transaction

from garimpei.domain.listing.coverage import Coverage
from garimpei.domain.listing.ports import ConfigurationReader
from garimpei.domain.listing.read_models import ListingReader, Observation
from garimpei.domain.listing.scope import Scope
from garimpei.domain.monitoring.errors import ConfigurationReadFailed
from garimpei.domain.monitoring.snapshot import MonitoringSnapshot
from garimpei.domain.valuation.ports import ValuationReader
from garimpei.domain.valuation.profit import ProfitInput
from garimpei.domain.valuation.profit_queries import ProfitReadFailed, UnsupportedProfitEvent
from garimpei.infra.persistence.listing_models import ListingEvent
from garimpei.infra.queries.listing.postgres_queries import _observation

logger = logging.getLogger("garimpei.profit")


class PostgresProfitQueries:
    def __init__(
        self,
        configuration: ConfigurationReader,
        listings: ListingReader,
        valuations: ValuationReader,
    ) -> None:
        self._configuration = configuration
        self._listings = listings
        self._valuations = valuations

    def read(self, identity: UUID, now: datetime, *, event: bool) -> ProfitInput | None:
        try:
            return self._consistent_read(identity, now, event)
        except (DatabaseError, ConfigurationReadFailed):
            logger.warning(
                "Profit dependency read failed",
                extra={
                    "event": "profit_read_failed",
                    "error_code": ProfitReadFailed.code,
                    "profit_identity": str(identity),
                },
            )
            raise ProfitReadFailed() from None

    def _consistent_read(self, identity: UUID, now: datetime, event: bool) -> ProfitInput | None:
        nested = connection.in_atomic_block
        with transaction.atomic():
            self._isolation(nested)
            config = self._configuration.execute()
            scope = Scope.from_snapshot(config)
            if event:
                return self._event(identity, now, config, scope)
            listing = self._listings.listing(identity, scope)
            if listing is None:
                return None
            return ProfitInput(
                listing.id,
                listing.observation,
                listing.current_coverage,
                listing.applicable_freight,
                config,
                self._valuations.current(listing.id, now),
            )

    @staticmethod
    def _isolation(nested: bool) -> None:
        with connection.cursor() as cursor:
            if not nested:
                cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
                return
            # Never silently produce a mixed snapshot inside a consumer's transaction.
            cursor.execute("SHOW transaction_isolation")
            if cursor.fetchone()[0] not in ("repeatable read", "serializable"):
                raise DatabaseError("Profit query requires a consistent outer transaction")

    def _event(
        self, identity: UUID, now: datetime, config: MonitoringSnapshot, scope: Scope | None
    ) -> ProfitInput | None:
        row = (
            ListingEvent.objects.select_related("observation__cycle__state")
            .filter(id=identity)
            .first()
        )
        if row is None:
            return None
        if row.kind not in ("discovered", "price_decreased"):
            raise UnsupportedProfitEvent(row.kind)
        observation = _observation(row.observation)
        applicable = scope is not None and (
            observation.scope_key == scope.key
            and row.observation.cycle.state.configuration_id == scope.configuration_id
        )
        coverage = (
            observation.coverage
            if applicable
            else Coverage("unknown", "unknown", None, "scope_changed", "scope_changed")
        )
        freight = self._event_freight(observation, config) if applicable else None
        return ProfitInput(
            row.listing_id,
            observation,
            coverage,
            freight,
            config,
            self._valuations.current(row.listing_id, now),
            row.id,
        )

    @staticmethod
    def _event_freight(observation: Observation, config: MonitoringSnapshot) -> "Decimal | None":
        return (
            observation.evidence.freight if observation.evidence.freight_cep == config.cep else None
        )
