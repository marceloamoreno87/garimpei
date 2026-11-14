"""A killed authorized sender cannot be reclaimed as an unsent request."""

import json
import os
import signal
import subprocess
from pathlib import Path

import pytest

from tests.factories.alert_scenario import add_cases, alert_scenario, alert_shell, wait_alerts
from tests.factories.operations_metrics import InstanceMeasurements, workload_signature
from tests.factories.runtime import pause_worker, resume_worker
from tests.factories.valuation import listing
from tests.integration.test_collection import command, completed, sql, wait_for


def test_sigkill_after_authorization_before_post_requires_reconciliation(tmp_path: Path) -> None:
    with alert_scenario(tmp_path, enabled=False) as (instance, source, clock, channel):
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
            "valuation for authorized-send cut",
            seconds=35,
        )
        worker_group = pause_worker(instance)
        process: subprocess.Popen[str] | None = None
        try:
            alert_shell(
                instance,
                """
from garimpei.main import build_read_listing_changes
page=build_read_listing_changes().execute()
store.ingest(page,clock())
prepare_first('903')
assert intent('903').state=='queued'
""",
            )
            marker = tmp_path / "authorization-committed"
            code = f"""
from pathlib import Path

import pytest

from tests.factories.operations_metrics import InstanceMeasurements, workload_signature
from time import sleep
from garimpei.domain.alert.alert import Binding
from garimpei.infra.persistence.alert_models import FirstAlertIdentity
from garimpei.main import build_alert_store,_listing_clock
from garimpei.config.env import load_listing_settings
row=FirstAlertIdentity.objects.get(listing__external_id='903')
delivery=build_alert_store().claim(row.intent_id,Binding('synthetic','100@c.us','200@c.us'),_listing_clock(load_listing_settings())(),reconcile=False)
assert delivery
Path({str(marker)!r}).write_text('authorized')
while True:sleep(1)
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
                "authorization boundary",
                seconds=20,
            )
            assert marker.exists() and process.poll() is None
            assert sql(
                instance, "SELECT count(*) FROM runtime_alertintent WHERE state='authorized'"
            ) == [(1,)]
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=10)
            assert process.returncode != 0 and not [
                call for call in channel.calls if call[0] == "POST"
            ]
            clock.advance(61)
            alert_shell(
                instance,
                """
row=intent('903')
assert row.state=='authorized'
original_body=row.body
recovered=store.claim(row.id,binding,clock(),reconcile=True)
assert recovered and recovered.reconcile and recovered.body==original_body
assert store.claim(row.id,binding,clock(),reconcile=False) is None
assert AlertAttempt.objects.filter(intent=row).count()==1
""",
            )
            assert not [call for call in channel.calls if call[0] == "POST"]
        finally:
            if process is not None and process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=10)
            resume_worker(worker_group)


@pytest.mark.parametrize("kill_worker", [False, True], ids=["control", "fault"])
def test_sigkill_after_confirmation_preserves_receipt_and_does_not_resend(
    tmp_path: Path, kill_worker: bool
) -> None:
    from garimpei.infra.runtime.processes import verify_process

    with alert_scenario(tmp_path) as (instance, source, clock, channel):
        with InstanceMeasurements(
            instance,
            tmp_path / "confirmation-measurements.json",
            mode="fault" if kill_worker else "control",
        ) as measurements:
            clock.advance(1)
            source.rows["935"] = listing(
                "935",
                "1000,00",
                published_at=clock.value.isoformat(),
                delivery=True,
                delivery_cep="01001000",
                pickup=False,
            )
            clock.advance(61)
            completed(instance, 2)
            wait_alerts(instance, 1, clock)
            confirmed = sql(
                instance,
                "SELECT id::text,confirmed_message FROM runtime_alertintent WHERE state='confirmed'",
            )
            assert len(confirmed) == 1 and len(channel.messages) == 1
            clock.advance(61)
            if kill_worker:
                owner = next(
                    record
                    for record in instance.manifest["processes"]
                    if "runworker" in record["command"]
                )
                verify_process(owner, instance.config.root)
                os.killpg(owner["pgid"], signal.SIGKILL)
                command(instance, "./scripts/stop.sh")
                command(instance, "./scripts/init.sh", "--disposable")
            # A collection admitted at restart owns its original publication window.
            # Wait for its checkpoint before presenting the next source snapshot.
            wait_for(
                lambda: (
                    sql(
                        instance,
                        "SELECT c.finished_at IS NOT NULL AND s.next_attempt_at > '"
                        + clock.value.isoformat()
                        + "'::timestamptz FROM runtime_collectionstate s "
                        "JOIN runtime_collectioncycle c ON c.id=s.current_id",
                    )
                    == [(True,)]
                ),
                "collection checkpoint before the next source input",
            )
            clock.advance(1)
            source.rows["936"] = listing(
                "936",
                "1000,00",
                published_at=clock.value.isoformat(),
                delivery=True,
                delivery_cep="01001000",
                pickup=False,
            )
            clock.advance(61)
            wait_alerts(instance, 2, clock)
            assert confirmed[0] in sql(
                instance,
                "SELECT id::text,confirmed_message FROM runtime_alertintent WHERE state='confirmed'",
            )
            assert len(channel.messages) == 2
            assert len([call for call in channel.calls if call[0] == "POST"]) == 2
            measurements.observed.update(
                offers=2,
                confirmed_posts=len(channel.messages),
                workload_signature=workload_signature(source.rows),
            )
        report = json.loads((tmp_path / "confirmation-measurements.json").read_text())
        assert report["offers"] == 2 and report["confirmed_posts"] == 2
        assert report["sampled_peak_database_bytes"] > 0
        assert report["sample_count"] > 1
        assert report["max_pending_jobs"] >= 0
        assert report["postgres_version"]


def test_sigkill_before_authorization_keeps_request_available(tmp_path: Path) -> None:
    with alert_scenario(tmp_path, enabled=False) as (instance, source, clock, channel):
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
            "valuation for pre-authorization cut",
            seconds=35,
        )
        worker_group = pause_worker(instance)
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
            marker = tmp_path / "before-authorization"
            code = f"""
from pathlib import Path

import pytest

from tests.factories.operations_metrics import InstanceMeasurements, workload_signature
from time import sleep
from garimpei.domain.alert.alert import Binding
from garimpei.infra.persistence.alert_models import FirstAlertIdentity
from garimpei.main import build_alert_store,_listing_clock
from garimpei.config.env import load_listing_settings
row=FirstAlertIdentity.objects.get(listing__external_id='903')
Path({str(marker)!r}).write_text('before authorization')
sleep(60)
build_alert_store().claim(row.intent_id,Binding('synthetic','100@c.us','200@c.us'),_listing_clock(load_listing_settings())(),reconcile=False)
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
                "pre-authorization boundary",
                seconds=20,
            )
            assert marker.exists() and process.poll() is None
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=10)
            alert_shell(
                instance,
                """
row=intent('903')
assert row.state=='queued' and not AlertAttempt.objects.filter(intent=row).exists()
delivery=store.claim(row.id,binding,clock(),reconcile=False)
assert delivery and not delivery.reconcile
assert AlertAttempt.objects.filter(intent=row).count()==1
""",
            )
            assert not [call for call in channel.calls if call[0] == "POST"]
        finally:
            if process is not None and process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=10)
            resume_worker(worker_group)
