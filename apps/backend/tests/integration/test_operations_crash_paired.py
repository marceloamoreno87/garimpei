"""Match source load and sender boundaries when measuring authorization crashes."""

import hashlib
import json
import os
import signal
import subprocess
from pathlib import Path

import pytest

from tests.factories.alert_scenario import add_cases, alert_scenario, alert_shell
from tests.factories.operations_metrics import InstanceMeasurements
from tests.factories.runtime import pause_worker, resume_worker
from tests.integration.test_collection import completed, sql, wait_for


@pytest.mark.parametrize("kill_sender", [False, True], ids=["control", "fault"])
@pytest.mark.parametrize("boundary", ["before", "after"])
def test_authorization_cut_has_same_workload_control(
    tmp_path: Path, boundary: str, kill_sender: bool
) -> None:
    with alert_scenario(tmp_path, enabled=False) as (instance, source, clock, channel):
        report_path = tmp_path / f"authorization-{boundary}-measurements.json"
        with InstanceMeasurements(
            instance, report_path, mode="fault" if kill_sender else "control"
        ) as measurements:
            add_cases(source, clock)
            clock.advance(61)
            completed(instance, 2)
            wait_for(
                lambda: (
                    sql(
                        instance,
                        "SELECT count(*) FROM runtime_valuationprogress p JOIN runtime_listing l "
                        "ON p.listing_id=l.id WHERE l.external_id='903' AND p.current_id IS NOT NULL",
                    )
                    == [(1,)]
                ),
                "same-load valuation before sender cut",
                seconds=35,
            )
            group = pause_worker(instance)
            process: subprocess.Popen[str] | None = None
            try:
                alert_shell(
                    instance,
                    """
from garimpei.main import build_read_listing_changes
store.ingest(build_read_listing_changes().execute(),clock())
prepare_first('903')
assert intent('903').state=='queued'
""",
                )
                marker, release = tmp_path / "sender-boundary", tmp_path / "release-sender"
                code = f"""
from pathlib import Path
from time import sleep
from garimpei.domain.alert.alert import Binding
from garimpei.infra.persistence.alert_models import FirstAlertIdentity
from garimpei.main import build_alert_store,_listing_clock,_effective_alert_settings,_alert_policy
from garimpei.infra.gateway.alert.waha_gateway import WahaGateway
from garimpei.config.env import load_listing_settings
row=FirstAlertIdentity.objects.get(listing__external_id='903')
store=build_alert_store()
binding=Binding('synthetic','100@c.us','200@c.us')
clock=_listing_clock(load_listing_settings())
delivery=None
if {boundary!r}=='after':
    delivery=store.claim(row.intent_id,binding,clock(),reconcile=False)
    assert delivery
Path({str(marker)!r}).write_text('ready')
while not Path({str(release)!r}).exists():sleep(.02)
if delivery is None:delivery=store.claim(row.intent_id,binding,clock(),reconcile=False)
assert delivery
settings=_effective_alert_settings()
gateway=WahaGateway(settings.url,settings.key,_alert_policy())
assert gateway.check(binding)
store.finish(delivery,gateway.send(delivery),clock())
"""
                process = subprocess.Popen(
                    [
                        "uv",
                        "run",
                        "--project",
                        "apps/backend",
                        "--frozen",
                        "--no-sync",
                        "python",
                        "apps/backend/manage.py",
                        "shell",
                        "-c",
                        code,
                    ],
                    cwd=instance.root,
                    env=instance.environment,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    start_new_session=True,
                )
                wait_for(
                    lambda: marker.exists() or process.poll() is not None,
                    f"{boundary} authorization matched boundary",
                    seconds=20,
                )
                assert marker.exists() and process.poll() is None
                if kill_sender:
                    os.killpg(process.pid, signal.SIGKILL)
                else:
                    release.write_text("continue")
                process.wait(timeout=10)
                assert process.returncode == (-signal.SIGKILL if kill_sender else 0)
                clock.advance(61)
                if kill_sender:
                    assert not [call for call in channel.calls if call[0] == "POST"]
                    alert_shell(
                        instance,
                        f"""
from garimpei.main import _effective_alert_settings,_alert_policy
from garimpei.infra.gateway.alert.waha_gateway import WahaGateway
row=intent('903')
original_body=row.body
assert row.state=={"queued" if boundary == "before" else "authorized"!r}
assert AlertAttempt.objects.filter(intent=row).count()=={0 if boundary == "before" else 1}
delivery=store.claim(row.id,binding,clock(),reconcile={boundary == "after"})
assert delivery and delivery.reconcile=={boundary == "after"}
assert delivery.binding==binding
if {boundary == "after"}:assert delivery.body==original_body
row.refresh_from_db()
assert delivery.body==row.body
if not delivery.reconcile:
    settings=_effective_alert_settings()
    gateway=WahaGateway(settings.url,settings.key,_alert_policy())
    assert gateway.check(binding)
    store.finish(delivery,gateway.send(delivery),clock())
assert AlertAttempt.objects.filter(intent=row).count()==1
assert store.claim(row.id,binding,clock(),reconcile=False) is None
""",
                    )
                expected_posts = 0 if kill_sender and boundary == "after" else 1
                assert len([call for call in channel.calls if call[0] == "POST"]) == expected_posts
                assert len(channel.messages) == expected_posts
                assert sql(
                    instance, "SELECT count(*) FROM runtime_alertintent WHERE state='confirmed'"
                ) == [(expected_posts,)]
                measurements.observed.update(
                    workload_signature=int(
                        hashlib.sha256(
                            json.dumps(source.rows, sort_keys=True).encode()
                        ).hexdigest()[:16],
                        16,
                    ),
                    offers=len(source.rows),
                    confirmed_posts=len(channel.messages),
                    authorized_attempts=1,
                    killed_senders=int(kill_sender),
                )
            finally:
                if process is not None and process.poll() is None:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=10)
                resume_worker(group)
        report = json.loads(report_path.read_text())
        assert report["sample_count"] > 1 and report["sampled_peak_database_bytes"] > 0
        assert report["offers"] == len(source.rows)
        assert report["confirmed_posts"] == expected_posts and report["authorized_attempts"] == 1
        assert report["killed_senders"] == int(kill_sender)
