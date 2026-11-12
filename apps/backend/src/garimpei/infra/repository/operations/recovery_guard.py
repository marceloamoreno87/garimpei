from pathlib import Path

from django.db import connection

from garimpei.infra.persistence.operations_models import RecoveryBarrier


def dispatch_blocked(installation: str, private_file: Path) -> bool:
    if private_file.exists():
        return True
    with connection.cursor() as cursor:
        cursor.execute("SELECT to_regclass('runtime_recoverybarrier')")
        row = cursor.fetchone()
    if row is None or row[0] is None:
        return False
    return RecoveryBarrier.objects.filter(installation=installation, state="blocked").exists()
