from pathlib import Path

import pytest

from tests.factories.first_eligibility import first_eligibility_scenario
from tests.factories.runtime import pause_worker, resume_worker
from tests.integration.test_collection import shell
from tests.integration.test_first_alert_review_regressions import PREPARE


@pytest.mark.parametrize("case", ["confirmed", "uncertain", "safe_retry", "expired"])
def test_robot_pause_orders_real_alert_authorization_and_preserves_reconciliation(
    tmp_path: Path, case: str
) -> None:
    with first_eligibility_scenario(tmp_path) as (instance, _, _, channel):
        group = pause_worker(instance)
        try:
            if case == "uncertain":
                channel.mode = "lost"
            script = """
from uuid import uuid4
from garimpei.main import build_robot_repository,build_read_robot_status,_effective_alert_settings,_alert_policy
from garimpei.domain.robot.control import RobotCommand
from garimpei.domain.alert.alert import Outcome
from garimpei.infra.gateway.alert.waha_gateway import WahaGateway
from garimpei.infra.persistence.robot_models import RobotOperation
robot=build_robot_repository(); status=build_read_robot_status()
s.publish(l.id,s.prepare(l.id),build_read_profit().execute(l.id),now)
r=FirstAlertIdentity.objects.get(listing=l); assert r.intent_id is not None
robot.command(RobotCommand(uuid4(),False,status.execute().revision))
before=r.intent.attempts.count()
assert store.claim(r.intent_id,binding,now,reconcile=False) is None
assert r.intent.attempts.count()==before
robot.command(RobotCommand(uuid4(),True,status.execute().revision))
"""
            if case == "expired":
                script += """
assert store.claim(r.intent_id,binding,now+timedelta(hours=49),reconcile=False) is None
r.intent.refresh_from_db();assert r.intent.reason=='publication_expired'
assert not r.intent.attempts.exists()
"""
            else:
                script += """
delivery=store.claim(r.intent_id,binding,now,reconcile=False); assert delivery
robot.command(RobotCommand(uuid4(),False,status.execute().revision))
assert status.execute().state=='draining'
settings=_effective_alert_settings(); gateway=WahaGateway(settings.url,settings.key,_alert_policy())
"""
                if case == "safe_retry":
                    script += """
store.finish(delivery,Outcome('safe_retry','not_transmitted'),now)
assert store.claim(r.intent_id,binding,now+timedelta(seconds=61),reconcile=False) is None
r.intent.refresh_from_db(); assert r.intent.state=='safe_retry' and r.intent.attempts.count()==1
"""
                else:
                    script += """
store.finish(delivery,gateway.send(delivery),now)
r.intent.refresh_from_db(); body=r.intent.body
"""
                    if case == "uncertain":
                        script += """
assert r.intent.state=='uncertain' and status.execute().state=='unknown'
recovered=store.claim(r.intent_id,Binding('changed','300@g.us','400@c.us'),now+timedelta(seconds=61),reconcile=True)
assert recovered and recovered.binding==binding and recovered.body==body
store.finish(recovered,gateway.reconcile(recovered,now+timedelta(seconds=61)),now+timedelta(seconds=61))
"""
                    script += """
r.intent.refresh_from_db(); assert r.intent.state=='confirmed'
assert r.intent.body==body and r.intent.attempts.count()==1
assert not RobotOperation.objects.filter(stage='alert',state__in=['active','unknown']).exists()
assert not status.execute().enabled
"""
            shell(instance, PREPARE + script)
            posts = [call for call in channel.calls if call[0] == "POST"]
            assert len(posts) == (0 if case in {"safe_retry", "expired"} else 1)
        finally:
            resume_worker(group)
