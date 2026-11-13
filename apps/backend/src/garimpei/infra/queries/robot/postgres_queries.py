from datetime import timedelta

from django.db import DatabaseError
from django.utils import timezone

from garimpei.domain.robot.control import RobotStatus, effective_state
from garimpei.domain.robot.errors import RobotUnavailable
from garimpei.infra.persistence.alert_models import AlertIntent
from garimpei.infra.persistence.inference_models import InferenceControl
from garimpei.infra.persistence.models import RuntimeState
from garimpei.infra.persistence.robot_models import RobotControl, RobotOperation


class PostgresRobotQueries:
    def status(self) -> RobotStatus:
        try:
            row = RobotControl.objects.get(pk="local")
            active = RobotOperation.objects.filter(installation=row, state="active").count()
            unknown = RobotOperation.objects.filter(installation=row, state="unknown").count()
            # Adoption must still expose legacy authorizations without inventing a permit.
            if not RobotOperation.objects.filter(stage="inference", state="active").exists():
                unknown += InferenceControl.objects.exclude(active_request=None).count()
            if not RobotOperation.objects.filter(stage="alert", state="active").exists():
                unknown += AlertIntent.objects.filter(state__in=["authorized", "uncertain"]).count()
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
