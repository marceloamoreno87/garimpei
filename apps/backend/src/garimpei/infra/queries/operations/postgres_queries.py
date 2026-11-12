"""Operational reads share one MVCC snapshot and never recompute business decisions."""

from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import cast
from uuid import UUID, uuid4

from django.db import connection, transaction
from django.db.models import F

from garimpei.domain.listing.ports import ConfigurationReader
from garimpei.domain.listing.scope import Scope
from garimpei.domain.operations.errors import OperationsError
from garimpei.infra.persistence.alert_models import (
    AlertEventDecision,
    AlertIntent,
    FirstEligibilityDecision,
)
from garimpei.infra.persistence.exploration_models import ExplorationOffer, ExplorationRevision
from garimpei.infra.persistence.listing_models import Listing, ListingObservation
from garimpei.infra.persistence.operations_models import OperationalUnit, RecoveryBarrier
from garimpei.infra.persistence.valuation_models import ValuationProgress
from garimpei.infra.repository.operations.progress_repository import restore_progress
from garimpei.infra.repository.valuation.mapper import decode_valuation

DEFINITIONS = {
    "stored": (
        "Armazenados",
        "Identidades distintas; inclui histórico fora dos interesses atuais.",
    ),
    "revalidated": ("Revalidados", "Observação confirmada no escopo e revisão atuais."),
    "with_detail": (
        "Com detalhe",
        "Detalhe confirmado para a observação atual; um card não basta.",
    ),
    "with_photo": ("Com foto", "Cópia de mídia utilizável da observação atual."),
    "recognized": ("Reconhecidos", "Identidade suficiente na avaliação aplicável persistida."),
    "with_sample": ("Com amostra", "Amostra equivalente e válida da mesma revisão."),
    "estimated": ("Estimados", "Composição calculável e aplicável publicada."),
    "eligible": (
        "Elegíveis",
        "Decisão atual de primeira elegibilidade ou redução autoriza alerta.",
    ),
    "confirmed": (
        "Envio confirmado",
        "Recibo aceito pelo servidor; não comprova entrega ou leitura.",
    ),
}


class PostgresOperationalQueries:
    def __init__(
        self,
        installation: str,
        recovery_file: Path,
        clock: Callable[[], datetime],
        configuration: ConfigurationReader,
        media_count: Callable[[tuple[UUID, ...]], int] | None = None,
    ) -> None:
        self._installation, self._file, self._clock = installation, recovery_file, clock
        self._configuration, self._media_count = configuration, media_count

    def read(self, interest: str | None = None) -> dict[str, object]:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
            return self._snapshot(interest)

    def _snapshot(self, interest: str | None) -> dict[str, object]:
        now = self._clock()
        configuration = self._configuration.execute()
        scope = Scope.from_snapshot(configuration)
        if interest and (scope is None or interest not in {s.interest.key for s in scope.searches}):
            raise OperationsError("operational_interest_invalid", 400)
        current = Listing.objects.select_related("latest__cycle").filter(latest__isnull=False)
        if scope is None:
            current = current.none()
        else:
            current = current.filter(
                latest__cycle__revision=scope.revision, latest__cycle__scope_key=scope.key
            )
        if interest:
            current = current.filter(latest__matches__key=interest).distinct()
        rows = tuple(current)
        identities = tuple(row.id for row in rows)
        values: dict[str, int | None] = self._counts(rows, now)
        values["with_photo"] = self._media_count(identities) if self._media_count else None
        barrier = RecoveryBarrier.objects.filter(
            installation=self._installation, state="blocked"
        ).first()
        return {
            "recovered_at": barrier.restored_at if barrier else None,
            "snapshot_id": str(uuid4()),
            "as_of": now,
            "scope_revision": configuration.revision,
            "observation_watermark": ListingObservation.objects.order_by("-observed_at", "-id")
            .values_list("id", flat=True)
            .first(),
            "interest": interest,
            "stages": self._stages(now),
            "counts": {
                key: {
                    "available": values[key] is not None,
                    "value": values[key],
                    "label": label,
                    "definition": description,
                }
                for key, (label, description) in DEFINITIONS.items()
            },
            "dispatch_suspended": self._file.exists()
            or RecoveryBarrier.objects.filter(
                installation=self._installation, state="blocked"
            ).exists(),
        }

    def _counts(self, rows: tuple[Listing, ...], now: datetime) -> dict[str, int | None]:
        identities = tuple(row.id for row in rows)
        latest = {row.id: row.latest for row in rows}
        recognized: set[UUID] = set()
        sampled: set[UUID] = set()
        for progress in ValuationProgress.objects.filter(listing_id__in=identities).select_related(
            "current"
        ):
            if progress.current is not None:
                _valuation_counts(progress, latest, now, recognized, sampled)
        estimated = _estimated(identities, latest, sampled)
        eligible = set(
            FirstEligibilityDecision.objects.filter(
                identity__listing_id__in=identities,
                generation=F("identity__generation"),
                observation_id=F("identity__listing__latest_id"),
                state="eligible",
            ).values_list("identity__listing_id", flat=True)
        )
        eligible.update(
            AlertEventDecision.objects.filter(
                event__listing_id__in=identities,
                event__observation_id=F("event__listing__latest_id"),
                state="eligible",
            ).values_list("event__listing_id", flat=True)
        )
        return {
            "stored": Listing.objects.count(),
            "revalidated": len(rows),
            "with_detail": sum(
                bool(r.latest and r.latest.evidence.get("source_available") is True) for r in rows
            ),
            "recognized": len(recognized),
            "with_sample": len(sampled),
            "estimated": len(estimated),
            "eligible": len(eligible),
            "confirmed": AlertIntent.objects.filter(state="confirmed").count(),
        }

    def _stages(self, now: datetime) -> list[dict[str, object]]:
        rows = OperationalUnit.objects.filter(installation=self._installation).order_by(
            "stage", "key"
        )
        stages = [_unit_view(row, now) for row in rows]
        known = {str(item["stage"]) for item in stages}
        for stage in (
            "listing",
            "valuation",
            "alert",
            "exploration",
            "maintenance",
            "inference",
            "media",
        ):
            if stage not in known:
                available = stage != "media" or self._media_count is not None
                stages.append(
                    {
                        "stage": stage,
                        "state": "idle" if available else "unavailable",
                        "reason": "historical_not_measured" if available else "stage_unavailable",
                        "last_progress_at": None,
                        "pending": None,
                        "action": None,
                    }
                )
        return stages


def _valuation_counts(
    progress: ValuationProgress,
    latest: dict[UUID, "ListingObservation | None"],
    now: datetime,
    recognized: set[UUID],
    sampled: set[UUID],
) -> None:
    assert progress.current is not None
    value = decode_valuation(cast(dict[str, object], progress.current.result))
    observation = latest[progress.listing_id]
    if observation is None or value.input_revision != observation.ordinal:
        return
    if value.product is not None:
        recognized.add(progress.listing_id)
    if (
        value.resale.price is not None
        and value.resale.valid_until
        and value.resale.valid_until > now
    ):
        sampled.add(progress.listing_id)


def _estimated(
    identities: tuple[UUID, ...],
    latest: dict[UUID, "ListingObservation | None"],
    sampled: set[UUID],
) -> set[UUID]:
    revision = ExplorationRevision.objects.order_by("-sequence").first()
    if revision is None:
        return set()
    rows = ExplorationOffer.objects.filter(
        revision=revision, listing_id__in=identities, profit__isnull=False
    )
    result: set[UUID] = set()
    for row in rows:
        observation = latest[row.listing_id]
        raw = row.payload.get("composition")
        composition = raw if isinstance(raw, dict) else {}
        if (
            observation is not None
            and row.listing_id in sampled
            and str(composition.get("observation_id")) == str(observation.id)
        ):
            result.add(row.listing_id)
    return result


def _unit_view(row: OperationalUnit, now: datetime) -> dict[str, object]:
    state = restore_progress(row)
    return {
        "id": str(row.id),
        "stage": row.stage,
        "key": row.key,
        "revision": row.revision,
        "state": state.state_at(now),
        "reason": row.reason,
        "last_progress_at": row.last_progress_at,
        "last_attempt_at": row.last_attempt_at,
        "pending": row.pending,
        "oldest_pending_at": row.pending_since if row.pending else None,
        "pending_age_seconds": max(0, (now - row.pending_since).total_seconds())
        if row.pending
        else 0,
        "next_attempt_at": row.next_attempt_at,
        "failures": row.failures,
        "action": "resume" if row.suspended and row.reason != "access_denied" else None,
    }
