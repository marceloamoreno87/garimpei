"""Integrity restoration never deactivates an already adopted authorization policy."""

import json
from typing import cast

from django.db import connection

from garimpei.infra.gateway.operations.archive_gateway import ArchiveInvalid
from garimpei.infra.persistence.gold_models import GoldPolicyAdoption
from garimpei.infra.persistence.operations_models import RecoveryBarrier


def prepare_gold_restore(files: dict[str, bytes]) -> None:
    rows = [json.loads(line) for line in files["runtime.goldpolicyadoption.jsonl"].splitlines()]
    if len(rows) != 1 or rows[0].get("pk") != "local":
        raise ArchiveInvalid("archive_gold_policy_missing")
    fields = cast(dict[str, object], rows[0]["fields"])
    active = GoldPolicyAdoption.objects.filter(installation="local", state="active").exists()
    if active and fields.get("state") != "active":
        raise ArchiveInvalid("archive_gold_policy_downgrade")
    if (
        not connection.in_atomic_block
        or not RecoveryBarrier.objects.filter(state="blocked").exists()
    ):
        raise ArchiveInvalid("archive_gold_restore_requires_recovery_barrier")
    # Only the transaction restoring an inspected archive may insert historical attempts.
    # Dispatch remains suspended by the independent F17 recovery barrier afterward.
    with connection.cursor() as cursor:
        cursor.execute("SELECT set_config('garimpei.integrity_restore','on',true)")
