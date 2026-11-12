import json
from pathlib import Path

from django.db import connection

from garimpei.infra.persistence.operations_models import RecoveryBarrier


def dispatch_blocked(installation: str, private_file: Path) -> bool:
    with connection.cursor() as cursor:
        cursor.execute("SELECT to_regclass('runtime_recoverybarrier')")
        exists = cursor.fetchone()
    if exists is None or exists[0] is None:
        return private_file.exists()
    barrier = RecoveryBarrier.objects.filter(installation=installation).first()
    if barrier is None:
        return private_file.exists()
    if barrier.state != "reconciled":
        return True
    try:
        marker = json.loads(private_file.read_text())
    except (OSError, ValueError):
        return True
    return (
        not isinstance(marker, dict)
        or marker.get("state") != "reconciled"
        or marker.get("backup_id") != str(barrier.backup_id)
    )
