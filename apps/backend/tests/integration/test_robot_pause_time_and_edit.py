from pathlib import Path

import pytest

from tests.factories.first_eligibility import first_eligibility_scenario
from tests.factories.runtime import pause_worker, resume_worker
from tests.integration.test_collection import command, shell
from tests.integration.test_first_alert_review_regressions import PREPARE


@pytest.mark.parametrize("expired", ["publication", "reference"])
def test_global_pause_does_not_extend_publication_or_reference_validity(
    tmp_path: Path, expired: str
) -> None:
    with first_eligibility_scenario(tmp_path) as (instance, _, clock, channel):
        group = pause_worker(instance)
        try:
            shell(
                instance,
                PREPARE
                + f"\nexpired={expired!r}\n"
                + """
from uuid import uuid4
from garimpei.main import build_robot_repository,build_read_robot_status
from garimpei.domain.robot.control import RobotCommand
from garimpei.infra.persistence.robot_models import RobotControl
if expired=='reference':
 progress=ValuationProgress.objects.select_related('current').get(listing=l)
 result=dict(progress.current.result);result['resale']=dict(result['resale'])
 result['resale']['valid_until']=(now+timedelta(seconds=1)).isoformat()
 progress.current.result=result;progress.current.save(update_fields=['result'])
s.publish(l.id,s.prepare(l.id),build_read_profit().execute(l.id),now)
intent=FirstAlertIdentity.objects.get(listing=l).intent
assert intent and intent.state=='queued'
robot=build_robot_repository();status=build_read_robot_status()
robot.command(RobotCommand(uuid4(),False,status.execute().revision))
""",
            )
            clock.advance(49 * 3600 if expired == "publication" else 2)
            shell(
                instance,
                PREPARE
                + f"\nexpired={expired!r}\n"
                + """
from uuid import uuid4
from garimpei.main import build_robot_repository,build_read_robot_status
from garimpei.domain.robot.control import RobotCommand
robot=build_robot_repository();status=build_read_robot_status()
assert not status.execute().enabled
robot.command(RobotCommand(uuid4(),True,status.execute().revision))
r=FirstAlertIdentity.objects.get(listing=l);intent=r.intent
assert store.claim(intent.id,binding,now,reconcile=False) is None
intent.refresh_from_db();assert not intent.attempts.exists()
if expired=='publication':assert intent.reason=='publication_expired'
else:
 assert build_read_profit().execute(l.id).resale.value is None
 assert ValuationProgress.objects.get(listing=l).current_id is not None
print('ROBOT_TIME_PRESERVED_PASS:'+expired)
""",
            )
            assert not [call for call in channel.calls if call[0] == "POST"]
        finally:
            resume_worker(group)


def test_configuration_edit_during_pause_and_normal_restart_preserve_pause_and_business_state(
    tmp_path: Path,
) -> None:
    with first_eligibility_scenario(tmp_path) as (instance, source, _, channel):
        group = pause_worker(instance)
        before_calls = list(source.calls)
        try:
            shell(
                instance,
                PREPARE
                + """
from uuid import uuid4
from garimpei.main import build_robot_repository,build_read_robot_status,build_monitoring_queries,build_monitoring_handler
from garimpei.domain.robot.control import RobotCommand
from garimpei.usecase.monitoring.save_step_usecase import StepInput
from garimpei.infra.persistence.inference_models import InferenceControl
robot=build_robot_repository();status=build_read_robot_status()
robot.command(RobotCommand(uuid4(),False,status.execute().revision))
configuration=build_monitoring_queries().read_form()
command=StepInput('editar',configuration.revision,cep=configuration.cep,shipping_estimate=str(configuration.shipping_estimate),resale_fee_percent='11.00',category_ids=tuple(i.key for i in configuration.interests if i.kind=='category'),product_names=tuple(i.label for i in configuration.interests if i.kind=='product'))
build_monitoring_handler()._update.execute(command)
assert build_monitoring_queries().read_form().resale_fee_percent==__import__('decimal').Decimal('11.00')
assert not status.execute().enabled and status.execute().revision==1
InferenceControl.objects.get_or_create(pk=1);InferenceControl.objects.filter(pk=1).update(paused=True)
print('ROBOT_EDIT_WHILE_PAUSED_PASS')
""",
            )
            resume_worker(group)
            group = 0
            command(instance, "./scripts/stop.sh")
            command(instance, "./scripts/init.sh", "--disposable")
            group = pause_worker(instance)
            shell(
                instance,
                """
from decimal import Decimal
from garimpei.main import build_read_robot_status,build_monitoring_queries
from garimpei.infra.persistence.inference_models import InferenceControl
from garimpei.infra.persistence.listing_models import Listing,ListingObservation
from garimpei.infra.persistence.robot_models import RobotControlCommand
status=build_read_robot_status().execute()
assert not status.enabled and status.revision==1
assert RobotControlCommand.objects.count()==1
assert build_monitoring_queries().read_form().resale_fee_percent==Decimal('11.00')
assert InferenceControl.objects.get(pk=1).paused
assert Listing.objects.count()==6 and ListingObservation.objects.count()>=6
print('ROBOT_RESTART_AFTER_EDIT_PASS')
""",
            )
            assert instance.http("/ofertas/")[0] == 200
            assert source.calls == before_calls
            assert not [call for call in channel.calls if call[0] == "POST"]
        finally:
            if group:
                resume_worker(group)
