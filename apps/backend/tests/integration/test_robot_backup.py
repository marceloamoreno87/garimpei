from tests.factories.runtime import FoundationInstance
from tests.integration.test_collection import shell
from tests.integration.test_operational_recovery import operational_instance as operational_instance


def test_business_backup_preserves_local_pause_commands_and_operation_ownership(
    operational_instance: FoundationInstance,
) -> None:
    shell(
        operational_instance,
        """
from uuid import uuid4
from garimpei.domain.robot.control import RobotCommand
from garimpei.infra.gateway.operations.snapshot_gateway import BusinessSnapshotGateway
from garimpei.infra.persistence.operations_models import BackupRecord
from garimpei.infra.persistence.robot_models import RobotControl, RobotControlCommand, RobotOperation
from garimpei.infra.repository.robot.postgres_repository import PostgresRobotRepository
from garimpei.main import build_backup_repository
repository=PostgresRobotRepository()
permit=repository.authorize('navigation','backup-local-operation','fixture-revision',1)
assert permit is not None
control=RobotControl.objects.get(pk='local')
repository.command(RobotCommand(uuid4(),False,control.revision))
before=[list(model.objects.values()) for model in (RobotControl,RobotControlCommand,RobotOperation)]
snapshot=BusinessSnapshotGateway().capture('f22-backup-regression')
try:
 assert 'runtime.listing.jsonl' in snapshot.files
 assert not any(name in snapshot.files for name in (
  'runtime.robotcontrol.jsonl','runtime.robotcontrolcommand.jsonl','runtime.robotoperation.jsonl'))
finally:snapshot.close()
identity=build_backup_repository().create()
assert identity and BackupRecord.objects.get(pk=identity).state=='completed'
assert before==[list(model.objects.values()) for model in (RobotControl,RobotControlCommand,RobotOperation)]
assert not RobotControl.objects.get(pk='local').requested_enabled
repository.complete(permit)
""",
    )
