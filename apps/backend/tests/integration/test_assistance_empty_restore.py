"""A background diagnostic projection must not populate a pristine restore target."""

from tests.factories.runtime import FoundationInstance


def test_idle_assistance_reconciliation_preserves_empty_business_restore_target(
    foundations: list[FoundationInstance],
) -> None:
    result = foundations[0].shell("""
from uuid import uuid4
from django.db import connection
from django.core.management import call_command
from garimpei.infra.gateway.operations.snapshot_gateway import BusinessSnapshotGateway
from garimpei.main import reconcile_assistance
original=connection.settings_dict['NAME']
database='garimpei_f23_empty_'+uuid4().hex[:12]
with connection.cursor() as cursor:cursor.execute('CREATE DATABASE '+connection.ops.quote_name(database))
try:
 connection.close();connection.settings_dict['NAME']=database
 call_command('migrate',interactive=False,verbosity=0)
 snapshot=BusinessSnapshotGateway()
 assert snapshot.is_empty()
 reconcile_assistance()
 assert snapshot.is_empty(),'idle worker assistance populated an otherwise empty restore target'
finally:
 connection.close();connection.settings_dict['NAME']=original
 with connection.cursor() as cursor:cursor.execute('DROP DATABASE '+connection.ops.quote_name(database)+' WITH (FORCE)')
""")
    assert result.returncode == 0, result.stdout + result.stderr
