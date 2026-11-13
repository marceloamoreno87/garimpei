from datetime import timedelta

from django.db import DatabaseError
from django.utils import timezone

from garimpei.domain.robot.control import RobotStatus, effective_state
from garimpei.domain.robot.errors import RobotUnavailable
from garimpei.infra.persistence.alert_models import AlertIntent
from garimpei.infra.persistence.inference_models import InferenceControl
from garimpei.infra.persistence.models import RuntimeState
from garimpei.infra.persistence.robot_models import RobotControl, RobotOperation
from garimpei.infra.repository.robot.ownership import owner_is_live


class PostgresRobotQueries:
    def status(self) -> RobotStatus:
        try:
            row = RobotControl.objects.get(pk="local")
            owners = list(
                RobotOperation.objects.filter(installation=row, state="active").values_list(
                    "worker_reference", flat=True
                )
            )
            active = sum(owner_is_live(owner) for owner in owners)
            unknown = (
                len(owners)
                - active
                + RobotOperation.objects.filter(installation=row, state="unknown").count()
            )
            # Match each legacy effect separately: a new permit for another effect
            # cannot conceal an older unresolved authorization in this installation.
            tracked_requests = set(
                RobotOperation.objects.filter(
                    installation=row, stage="inference", state__in=["active", "unknown"]
                ).values_list("input_revision", flat=True)
            )
            unknown += sum(
                str(request) not in tracked_requests
                for request in InferenceControl.objects.exclude(active_request=None).values_list(
                    "active_request", flat=True
                )
            )
            tracked_alerts = set(
                RobotOperation.objects.filter(
                    installation=row, stage="alert", state__in=["active", "unknown"]
                ).values_list("unit_key", flat=True)
            )
            unknown += sum(
                str(identity) not in tracked_alerts
                for identity in AlertIntent.objects.filter(
                    state__in=["authorized", "uncertain"]
                ).values_list("id", flat=True)
            )
            worker = RuntimeState.objects.filter(
                stopped_at=None, last_probe_at__gte=timezone.now() - timedelta(seconds=30)
            ).exists()
            return RobotStatus(
                row.requested_enabled,
                row.revision,
                row.changed_at,
                effective_state(row.requested_enabled, active, unknown),
                active,
                unknown,
                worker,
            )
        except (DatabaseError, RobotControl.DoesNotExist) as error:
            raise RobotUnavailable() from error
