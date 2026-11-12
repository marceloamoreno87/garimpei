from uuid import UUID

from django.db import DatabaseError, transaction
from django.utils import timezone

from garimpei.domain.listing.condition import Choice
from garimpei.domain.listing.condition_ports import (
    ConditionConflict,
    ConditionNotFound,
    ConditionSaveFailed,
)
from garimpei.infra.persistence.alert_models import ManualConditionHistory
from garimpei.infra.persistence.listing_models import Listing, ManualCondition
from garimpei.infra.persistence.monitoring_unit_of_work import lock_monitoring_publication
from garimpei.infra.repository.listing.condition_mapper import condition_state


class PostgresConditionRepository:
    def save(self, identity: UUID, choice: Choice, revision: int) -> int:
        try:
            with transaction.atomic(durable=True):
                lock_monitoring_publication()
                return self._save_locked(identity, choice, revision)
        except DatabaseError as error:
            raise ConditionSaveFailed() from error

    def _save_locked(self, identity: UUID, choice: Choice, revision: int) -> int:
        row = (
            Listing.objects.select_related("latest", "manual_condition").filter(id=identity).first()
        )
        if row is None or row.latest is None:
            raise ConditionNotFound()
        current = condition_state(row)
        if revision != current.revision or not current.editable:
            raise ConditionConflict()
        if current.manual == choice:
            return revision
        ManualCondition.objects.update_or_create(
            listing=row,
            defaults={
                "choice": choice,
                "revision": revision + 1,
                "updated_at": timezone.now(),
            },
        )
        row.publication_order += 1
        row.save(update_fields=["publication_order"])
        ManualConditionHistory.objects.create(
            listing=row,
            publication_order=row.publication_order,
            choice=choice,
            revision=revision + 1,
            confirmed_at=timezone.now(),
        )
        return revision + 1
