from pathlib import Path

import pytest

from tests.factories.first_eligibility import first_eligibility_scenario
from tests.factories.runtime import pause_worker, resume_worker
from tests.integration.test_collection import shell
from tests.integration.test_first_alert_review_regressions import PREPARE


@pytest.mark.parametrize("winner", ["pause", "authorization"])
def test_concurrent_workers_observe_one_pause_authorization_order(
    tmp_path: Path, winner: str
) -> None:
    with first_eligibility_scenario(tmp_path) as (instance, _, _, channel):
        group = pause_worker(instance)
        try:
            shell(
                instance,
                PREPARE
                + f"\nwinner={winner!r}\n"
                + """
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from django.db import connections
from uuid import uuid4
from garimpei.main import build_robot_repository,build_read_robot_status,_effective_alert_settings,_alert_policy
from garimpei.domain.robot.control import RobotCommand
from garimpei.infra.repository.robot.postgres_repository import PostgresRobotRepository
from garimpei.infra.gateway.alert.waha_gateway import WahaGateway
robot=build_robot_repository();status=build_read_robot_status()
s.publish(l.id,s.prepare(l.id),build_read_profit().execute(l.id),now)
intent=FirstAlertIdentity.objects.get(listing=l).intent
assert intent and intent.state=='queued'
held,release,other_started=Event(),Event(),Event()
def hold_clock():
 held.set();assert release.wait(8),'barrier timed out'
 return now
class HoldingAdmission:
 def authorize(self,*args):
  value=robot.authorize(*args)
  held.set();assert release.wait(8),'authorization barrier timed out'
  return value
 def complete(self,*args):return robot.complete(*args)
def pause():
 try:
  if winner=='authorization':other_started.set()
  repository=PostgresRobotRepository(hold_clock) if winner=='pause' else robot
  repository.command(RobotCommand(uuid4(),False,0))
 finally:connections.close_all()
def claim():
 try:
  if winner=='pause':other_started.set()
  repository=build_alert_store()
  if winner=='authorization':repository._robot=HoldingAdmission()
  return repository.claim(intent.id,binding,now,reconcile=False)
 finally:connections.close_all()
with ThreadPoolExecutor(max_workers=2) as pool:
 first=pool.submit(pause if winner=='pause' else claim)
 assert held.wait(8),'winner did not reach its transactional barrier'
 second=pool.submit(claim if winner=='pause' else pause)
 assert other_started.wait(8)
 release.set()
 first_result,second_result=first.result(timeout=10),second.result(timeout=10)
delivery=second_result if winner=='pause' else first_result
assert not status.execute().enabled
intent.refresh_from_db()
if winner=='pause':
 assert delivery is None and intent.attempts.count()==0 and intent.failures==0
 assert intent.state=='queued'
else:
 assert delivery and intent.attempts.count()==1 and intent.state=='authorized'
 body=intent.body
 settings=_effective_alert_settings();gateway=WahaGateway(settings.url,settings.key,_alert_policy())
 store.finish(delivery,gateway.send(delivery),now)
 intent.refresh_from_db();assert intent.state=='confirmed' and intent.body==body
 assert intent.attempts.count()==1
 assert store.claim(intent.id,binding,now+timedelta(seconds=61),reconcile=False) is None
print('ROBOT_CONCURRENT_ORDER_PASS:'+winner)
""",
            )
            assert len([call for call in channel.calls if call[0] == "POST"]) == (
                winner == "authorization"
            )
        finally:
            resume_worker(group)
