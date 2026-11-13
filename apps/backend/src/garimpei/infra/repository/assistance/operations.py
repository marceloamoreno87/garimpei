"""Worker-side snapshots expose only a finite whitelist; never logs or credentials."""

from django.db import transaction
from django.db.models import Max

from garimpei.infra.gateway.assistance.snapshots import digest
from garimpei.infra.persistence.assistance_models import AssistanceOperationsSnapshot
from garimpei.infra.persistence.monitoring_unit_of_work import lock_monitoring_publication
from garimpei.infra.persistence.operations_models import OperationalUnit

ACTIONS = {
    "access_suspended": "check_integrations",
    "login_required": "check_integrations",
    "gpu_unavailable": "check_local_ai",
    "out_of_memory": "check_local_ai",
    "execution_unknown": "recover_local_ai",
    "paused": "review_robot_control",
    "pending": "wait_for_work",
    "completed": "wait_for_work",
}


@transaction.atomic
def capture_operations_snapshot() -> AssistanceOperationsSnapshot:
    lock_monitoring_publication()
    values = list(
        OperationalUnit.objects.order_by("stage", "key").values(
            "stage", "reason", "revision", "pending", "suspended"
        )[:100]
    )
    facts = [
        dict(
            id=f"operation-{i}",
            field="action",
            value=ACTIONS.get(str(value["reason"]), "check_integrations"),
            source="sanitized_operations",
            stage=str(value["stage"])
            if str(value["stage"])
            in {"listing", "media", "inference", "alert", "valuation", "maintenance"}
            else "other",
            reason=str(value["reason"]) if str(value["reason"]) in ACTIONS else "unavailable",
            pending=int(value["pending"]),
            revision=int(value["revision"]),
            suspended=bool(value["suspended"]),
        )
        for i, value in enumerate(values)
    ]
    if not facts:
        facts = [
            dict(
                id="operation-empty",
                field="action",
                value="wait_for_work",
                source="sanitized_operations",
                pending=0,
            )
        ]
    signature = digest(facts)
    current = AssistanceOperationsSnapshot.objects.order_by("-revision").first()
    if current and digest(current.facts) == signature:
        return current
    revision = (
        AssistanceOperationsSnapshot.objects.aggregate(value=Max("revision"))["value"] or 0
    ) + 1
    return AssistanceOperationsSnapshot.objects.create(
        revision=revision, content_hash=digest(dict(facts=facts, revision=revision)), facts=facts
    )
