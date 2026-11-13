from datetime import datetime
from uuid import UUID

from django.db import transaction
from django.db.models import F, Q

from garimpei.domain.valuation.identification_values import AttributeConflict
from garimpei.domain.valuation.identity_errors import (
    IdentityConflict,
    IdentityNotFound,
    InvalidIdentityCombination,
)
from garimpei.domain.valuation.identity_ports import IdentityEdit, IdentityView
from garimpei.domain.valuation.manual_identity import ManualIdentity
from garimpei.domain.valuation.ports import Clock
from garimpei.infra.persistence.identity_models import (
    IdentityProgress,
    ManualIdentityRevision,
    ProductIdentification,
)
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.persistence.monitoring_unit_of_work import lock_monitoring_publication
from garimpei.infra.persistence.valuation_models import ValuationProgress
from garimpei.infra.repository.alert.first_inputs import invalidate_first_alert
from garimpei.infra.repository.robot.postgres_repository import robot_enabled
from garimpei.infra.repository.valuation.identity_mapper import (
    decode_identity,
    encode_identity,
    identify_row,
    manual_value,
)


class PostgresIdentityRepository:
    def __init__(self, clock: Clock) -> None:
        self._clock = clock

    def read(self, identity: UUID) -> IdentityView | None:
        row = (
            Listing.objects.select_related("latest", "identity_progress__manual__observation")
            .filter(id=identity)
            .first()
        )
        if row is None or row.latest is None:
            return None
        progress = getattr(row, "identity_progress", None)
        result = identify_row(row, progress)
        manual = manual_value(progress)
        history = tuple(
            decode_identity(item.result)
            for item in ProductIdentification.objects.filter(listing=row).order_by("recorded_at")
        )
        return IdentityView(row.id, result, manual.values if manual else (), history)

    @transaction.atomic
    def save(self, command: IdentityEdit) -> IdentityView:
        lock_monitoring_publication()
        row = (
            Listing.objects.select_for_update(of=("self",))
            .select_related("latest")
            .filter(id=command.listing_id)
            .first()
        )
        if row is None or row.latest is None:
            raise IdentityNotFound()
        progress, _ = IdentityProgress.objects.get_or_create(listing=row)
        if (
            command.observed_revision != row.latest.ordinal
            or command.manual_revision != progress.manual_revision
        ):
            raise IdentityConflict()
        now = self._clock()
        previous = manual_value(progress)
        before = identify_row(row, progress)
        value = self._edit(command, previous, before.conflicts, now)
        revision = ManualIdentityRevision.objects.create(
            listing=row,
            revision=progress.manual_revision + 1,
            observation=row.latest,
            action=command.action,
            resolution=command.resolution or "",
            values=dict(value.values) if value else {},
            reviewed_conflicts=list(value.reviewed_conflicts) if value else [],
            recorded_at=now,
            previous=progress.manual,
        )
        progress.manual, progress.manual_revision = revision, revision.revision
        progress.save(update_fields=["manual", "manual_revision"])
        self._persist(row, progress, now)
        ValuationProgress.objects.filter(listing=row).update(signature="", due_at=now)
        invalidate_first_alert(row.id, now)
        result = self.read(row.id)
        assert result is not None
        return result

    @staticmethod
    def _edit(
        command: IdentityEdit,
        previous: ManualIdentity | None,
        conflicts: tuple[AttributeConflict, ...],
        now: datetime,
    ) -> ManualIdentity | None:
        if command.action == "resolve" and command.resolution == "keep_manual":
            if previous is None or not conflicts:
                raise InvalidIdentityCombination(
                    "Nenhum conflito manual vigente foi apresentado para revisão."
                )
            return previous.review(
                conflicts, reviewed_revision=command.observed_revision, recorded_at=now
            )
        if command.action == "resolve" and command.resolution == "use_observed":
            return None
        if command.action == "resolve" and command.resolution != "correct":
            raise InvalidIdentityCombination(
                "Resolução esperada: keep_manual, use_observed ou correct."
            )
        return ManualIdentity.create(
            dict(command.values),
            revision=command.manual_revision + 1,
            reviewed_revision=command.observed_revision,
            recorded_at=now,
        )

    def reconcile(self) -> None:
        pending = (
            Listing.objects.filter(latest__isnull=False)
            .filter(
                Q(identity_progress__current__isnull=True)
                | ~Q(identity_progress__current__observation_id=F("latest_id"))
            )
            .values_list("id", flat=True)[:100]
        )
        for identity in pending:
            self._record(identity)

    @transaction.atomic
    def _record(self, identity: UUID) -> None:
        lock_monitoring_publication()
        if not robot_enabled():
            return
        row = (
            Listing.objects.select_for_update(of=("self",))
            .select_related("latest")
            .get(id=identity)
        )
        progress, _ = IdentityProgress.objects.get_or_create(listing=row)
        self._persist(row, progress, self._clock())

    @staticmethod
    def _persist(row: Listing, progress: IdentityProgress, now: datetime) -> None:
        value = identify_row(row, progress)
        snapshot, _ = ProductIdentification.objects.get_or_create(
            listing=row,
            observation_id=value.observation_id,
            manual_revision=value.manual_revision,
            policy=value.policy_version,
            defaults=dict(
                state=value.state,
                product_key=value.product_key,
                result=encode_identity(value),
                recorded_at=now,
            ),
        )
        progress.current = snapshot
        progress.save(update_fields=["current"])
