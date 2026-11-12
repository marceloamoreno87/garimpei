from uuid import UUID

from django.db import DatabaseError, transaction

from garimpei.domain.listing.condition_ports import ConditionError, ConditionView
from garimpei.domain.listing.coverage import Coverage
from garimpei.domain.listing.ports import ConfigurationReader
from garimpei.domain.listing.scope import Scope
from garimpei.domain.monitoring.errors import ConfigurationReadFailed
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.persistence.monitoring_unit_of_work import lock_monitoring_publication
from garimpei.infra.repository.listing.condition_mapper import condition_state
from garimpei.infra.repository.listing.mapper import decode_evidence


class PostgresConditionQueries:
    def __init__(self, configuration: ConfigurationReader) -> None:
        self._configuration = configuration

    def read(self, identity: UUID) -> ConditionView | None:
        return next(iter(self._read(identity)), None)

    def all_visible(self) -> tuple[ConditionView, ...]:
        return tuple(view for view in self._read(None) if view.visible)

    def _read(self, identity: UUID | None) -> tuple[ConditionView, ...]:
        try:
            with transaction.atomic():
                lock_monitoring_publication()
                return self._snapshot(identity)
        except (DatabaseError, ConfigurationReadFailed) as error:
            raise ConditionError() from error

    def _snapshot(self, identity: UUID | None) -> tuple[ConditionView, ...]:
        scope = Scope.from_snapshot(self._configuration.execute())
        rows = Listing.objects.select_related("latest__cycle__state", "manual_condition").exclude(
            latest=None
        )
        if identity is not None:
            rows = rows.filter(id=identity)
        return tuple(self._view(row, scope) for row in rows.order_by("-first_seen_at", "id"))

    @staticmethod
    def _view(row: Listing, scope: Scope | None) -> ConditionView:
        assert row.latest is not None
        observation = row.latest
        evidence = decode_evidence(observation.evidence)
        current = (
            scope is not None
            and scope.key == observation.cycle.scope_key
            and scope.configuration_id == observation.cycle.state.configuration_id
        )
        visible = (
            current
            and evidence.source_available is not False
            and Coverage(**observation.coverage).status != "excluded"
        )
        return ConditionView(
            row.id,
            row.external_id,
            row.source,
            row.canonical_url,
            evidence.title or "Anúncio sem título informado",
            evidence,
            condition_state(row),
            observation.observed_at,
            observation.price,
            visible,
        )
