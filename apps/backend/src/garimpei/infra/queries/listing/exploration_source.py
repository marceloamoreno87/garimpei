from datetime import datetime
from typing import cast

from django.db.models import Max

from garimpei.domain.listing.condition import ConditionState, automatic_condition, normalized
from garimpei.domain.listing.coverage import Coverage
from garimpei.domain.listing.exploration import Offer
from garimpei.domain.listing.listing import InterestKind, Match
from garimpei.domain.listing.ports import ConfigurationReader
from garimpei.domain.listing.read_models import Observation
from garimpei.domain.listing.scope import Scope
from garimpei.domain.valuation.profit import ProfitInput, compose_profit
from garimpei.infra.persistence.listing_models import Listing, ListingObservation
from garimpei.infra.queries.valuation.postgres_queries import PostgresValuationQueries
from garimpei.infra.repository.listing.mapper import decode_evidence


class ExplorationSource:
    def __init__(
        self,
        configuration: ConfigurationReader,
        valuations: PostgresValuationQueries,
        labels: dict[str, str],
    ) -> None:
        self._configuration = configuration
        self._valuations = valuations
        self._labels = labels

    def snapshot(self, now: datetime) -> tuple[Offer, ...]:
        config = self._configuration.execute()
        scope = Scope.from_snapshot(config)
        rows = tuple(
            Listing.objects.select_related("latest__cycle__state")
            .defer(
                "latest__cycle__results",
                "latest__cycle__planned",
                "latest__cycle__diagnostics",
                "latest__cycle__window_evidence",
                "latest__cycle__origin",
            )
            .exclude(latest=None)
            .prefetch_related("latest__matches")
            .order_by("id")
        )
        valid = {
            r["listing_id"]: r["at"]
            for r in ListingObservation.objects.filter(evidence__source_available=True)
            .values("listing_id")
            .annotate(at=Max("observed_at"))
        }
        values = self._valuations.current_many(rows, now)
        return tuple(
            self._offer(row, scope, config, values[row.id], now, valid.get(row.id)) for row in rows
        )

    def search_text(self, value: Offer) -> str:
        return normalized(
            value.title + " " + " ".join(self._labels.get(key, key) for key in value.categories)
        )

    @staticmethod
    def _offer(
        row: Listing,
        scope: Scope | None,
        config: "MonitoringSnapshot",
        valuation: "Valuation",
        now: datetime,
        last_valid: datetime | None,
    ) -> Offer:
        raw = row.latest
        assert raw is not None
        evidence = decode_evidence(raw.evidence)
        current = (
            scope is not None
            and scope.key == raw.cycle.scope_key
            and scope.configuration_id == raw.cycle.state.configuration_id
        )
        coverage = (
            Coverage(**raw.coverage)
            if current
            else Coverage("unknown", "unknown", None, "scope_changed", "scope_changed")
        )
        observation = Observation(
            raw.id,
            raw.observed_at,
            raw.cycle.revision,
            raw.cycle.scope_key,
            evidence,
            coverage,
            tuple(raw.provenance.items()),
            tuple(Match(cast(InterestKind, m.kind), m.key) for m in raw.matches.all()),
        )
        unavailable = evidence.source_available is False
        return Offer(
            row.id,
            row.external_id,
            row.source,
            row.canonical_url,
            row.first_seen_at,
            raw.observed_at,
            evidence,
            ConditionState(automatic_condition(evidence)),
            tuple(sorted(m.key for m in observation.interests if m.kind == "category")),
            coverage.pickup == "confirmed",
            coverage.shipping == "confirmed",
            current and bool(observation.interests) and not unavailable,
            compose_profit(
                ProfitInput(
                    row.id,
                    observation,
                    coverage,
                    evidence.freight if evidence.freight_cep == config.cep else None,
                    config,
                    valuation,
                ),
                now,
            ),
            valuation,
            unavailable,
            last_valid,
            raw.id,
        )


from garimpei.domain.monitoring.snapshot import MonitoringSnapshot  # noqa: E402
from garimpei.domain.valuation.values import Valuation  # noqa: E402
