"""Persistent adoption fence shared with final authorizations, including incompatible workers."""

from datetime import datetime
from typing import cast

from django.db import transaction
from django.db.models import Count

from garimpei.domain.alert.gold_evidence import POLICY
from garimpei.infra.persistence.alert_models import AlertIntent
from garimpei.infra.persistence.gold_models import GoldPolicyAdoption
from garimpei.infra.persistence.monitoring_unit_of_work import lock_monitoring_publication
from garimpei.infra.repository.robot.locking import lock_robot_control


def gold_active() -> bool:
    # The migration creates this row. An unexpected absence is a failure, not legacy fallback.
    row = GoldPolicyAdoption.objects.get(installation="local")
    if row.policy != POLICY or row.consumer_version != POLICY:
        raise ValueError("gold policy: expected gold-alert-v1 compatible installation")
    if row.state == "active" and row.activated_at is None:
        raise ValueError("gold policy active: expected persisted activation timestamp")
    return row.state == "active"


def adopt_gold_policy(now: datetime) -> dict[str, object]:
    with transaction.atomic():
        lock_robot_control()
        lock_monitoring_publication()
        row = GoldPolicyAdoption.objects.select_for_update().get(installation="local")
        if row.state == "active":
            return cast(dict[str, object], row.inventory)
        # Keep uncertain/authorized attempts exactly as recorded; only new authorizations change.
        inventory: dict[str, object] = {
            "states": {
                item["state"]: item["count"]
                for item in AlertIntent.objects.values("state").annotate(count=Count("id"))
            },
            "intent_count": AlertIntent.objects.count(),
            "possible_transmission_count": AlertIntent.objects.filter(
                state__in=["authorized", "uncertain", "review"]
            ).count(),
            "adopted_at": now.isoformat(),
            "compatible_consumer": POLICY,
        }
        row.policy, row.consumer_version, row.state = POLICY, POLICY, "active"
        row.activated_at, row.inventory = now, inventory
        row.save()
        return inventory


class PostgresGoldPolicyRepository:
    def adopt(self, now: datetime) -> dict[str, object]:
        return adopt_gold_policy(now)
