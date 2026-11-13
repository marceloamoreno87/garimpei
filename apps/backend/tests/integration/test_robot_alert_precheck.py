from pathlib import Path

import pytest

from tests.factories.first_eligibility import first_eligibility_scenario
from tests.factories.runtime import pause_worker, resume_worker
from tests.integration.test_collection import shell
from tests.integration.test_first_alert_review_regressions import PREPARE


@pytest.mark.parametrize("case", ["missing_binding", "pause_during_check"])
def test_paused_alert_precheck_never_spends_failures_or_changes_schedule(
    tmp_path: Path, case: str
) -> None:
    with first_eligibility_scenario(tmp_path) as (instance, _, _, channel):
        group = pause_worker(instance)
        try:
            shell(
                instance,
                PREPARE
                + f"\ncase={case!r}\n"
                + """
from uuid import uuid4
from garimpei.main import build_robot_repository,build_read_robot_status,build_read_listing_changes
from garimpei.domain.robot.control import RobotCommand
from garimpei.usecase.alert.send_alert_usecase import SendAlertUseCase
robot=build_robot_repository();status=build_read_robot_status()
s.publish(l.id,s.prepare(l.id),build_read_profit().execute(l.id),now)
intent=FirstAlertIdentity.objects.get(listing=l).intent
before=(intent.failures,intent.next_action,intent.state,intent.reason,intent.attempts.count())
class PausingUnavailableChannel:
 def check(self, binding):
  robot.command(RobotCommand(uuid4(),False,status.execute().revision))
  return False
 def send(self, delivery):raise AssertionError('No send after failed check')
if case=='missing_binding':robot.command(RobotCommand(uuid4(),False,status.execute().revision))
SendAlertUseCase(store,PausingUnavailableChannel(),None if case=='missing_binding' else binding,build_read_listing_changes(),lambda:now).execute()
intent.refresh_from_db()
assert not status.execute().enabled
assert (intent.failures,intent.next_action,intent.state,intent.reason,intent.attempts.count())==before
print('ROBOT_ALERT_PRECHECK_PASS:'+case)
""",
            )
            assert not [call for call in channel.calls if call[0] == "POST"]
        finally:
            resume_worker(group)
