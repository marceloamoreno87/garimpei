import json
from pathlib import Path

from tests.factories.first_eligibility import first_eligibility_scenario
from tests.factories.operations_evidence import serve_recovery_evidence
from tests.factories.runtime import pause_worker, prepare_instance, resume_worker
from tests.integration.test_collection import command, shell
from tests.integration.test_first_alert_review_regressions import PREPARE


def test_old_copy_requires_complete_inventory_and_original_receipt_before_release(
    tmp_path: Path,
) -> None:
    source_private = tmp_path / "source"
    source_private.mkdir()
    with first_eligibility_scenario(source_private) as (source, _, _, channel):
        with source.private_file.open("a") as output:
            output.write(f"GARIMPEI_BACKUP_DIR={tmp_path / 'backups'}\n")
        group = pause_worker(source)
        target = prepare_instance(
            source.root, tmp_path, "f17_reconcile_" + source.config.instance[-8:]
        )
        proof: dict[str, object] = {}
        try:
            shell(
                source,
                PREPARE
                + """
import json
from garimpei.main import build_backup_repository,_effective_alert_settings,_alert_policy
from garimpei.config.env import load_operations_settings,load_config
from garimpei.infra.gateway.alert.waha_gateway import WahaGateway
from garimpei.infra.persistence.operations_models import BackupRecord
s.publish(l.id,s.prepare(l.id),build_read_profit().execute(l.id),now)
identity=FirstAlertIdentity.objects.get(listing=l).intent_id
assert identity
claim=store.claim(identity,binding,now,reconcile=False);assert claim
r=build_backup_repository();copy_id=r.create();record=BackupRecord.objects.get(id=copy_id)
settings=load_operations_settings();alerts=_effective_alert_settings()
channel=WahaGateway(alerts.url,alerts.key,_alert_policy())
outcome=channel.send(claim);assert outcome.state=='confirmed'
store.finish(claim,outcome,now)
entries=[]
for row in AlertIntent.objects.all():
 attempt=row.attempts.order_by('-ordinal').first()
 entries.append({'id':str(row.id),'state':row.state,'body':row.body,'session':row.session,'recipient':row.recipient,'account':row.account,'attempt_id':str(attempt.id) if attempt else None,'message_id':row.confirmed_message})
proof={'format_version':1,'complete':True,'source_installation':load_config().environment_id,'backup_id':str(copy_id),'snapshot_at':record.snapshot_at.isoformat(),'intents':entries}
(settings.backup_dir/'proof.json').write_text(json.dumps({'proof':proof,'archive':str(settings.backup_dir/record.file_key),'channel_url':alerts.url}))
""",
            )
            data = json.loads((tmp_path / "backups/proof.json").read_text())
            proof.update(data["proof"])
            assert len(channel.messages) == 1
            messages = channel.messages.copy()
            with serve_recovery_evidence(proof) as evidence_url:
                with target.private_file.open("a") as output:
                    output.write(
                        f"GARIMPEI_BACKUP_DIR={tmp_path / 'restored-backups'}\nGARIMPEI_AI_SERVICE_ENABLED=false\nGARIMPEI_ALERTS_ENABLED=false\nGARIMPEI_RECOVERY_EVIDENCE_FIXTURE_URL={evidence_url}\nGARIMPEI_ALERT_FIXTURE_URL={data['channel_url']}\nGARIMPEI_WAHA_SESSION=synthetic\nGARIMPEI_WAHA_ACCOUNT=200@c.us\nGARIMPEI_WAHA_RECIPIENT=100@g.us\n"
                    )
                command(target, "./scripts/init.sh", "--disposable")
                target_group = pause_worker(target)
                try:
                    shell(
                        target,
                        f"from garimpei.main import build_backup_repository;build_backup_repository().restore({data['archive']!r},isolated=True)",
                    )
                    args = (
                        "uv",
                        "run",
                        "--project",
                        "apps/backend",
                        "--frozen",
                        "--no-sync",
                        "python",
                        "apps/backend/manage.py",
                        "operational_backup",
                        "verify",
                        "--id",
                        str(proof["backup_id"]),
                    )
                    proof["complete"] = False
                    failed = target.command(*args)
                    assert (
                        failed.returncode == 1 and "recovery_evidence_incomplete" in failed.stderr
                    )
                    proof["complete"] = True
                    channel.messages.clear()
                    failed = target.command(*args)
                    assert (
                        failed.returncode == 1
                        and "recovery_channel_history_incomplete" in failed.stderr
                    )
                    shell(
                        target,
                        "from garimpei.main import build_recovery_guard;assert build_recovery_guard()()",
                    )
                    channel.messages[:] = messages
                    passed = target.command(*args)
                    assert passed.returncode == 0, passed.stdout + passed.stderr
                    shell(
                        target,
                        "from garimpei.main import build_recovery_guard;from garimpei.infra.persistence.alert_models import AlertIntent;assert not build_recovery_guard()();assert AlertIntent.objects.get().state=='confirmed'",
                    )
                    assert sum(method == "POST" for method, _ in channel.calls) == 1
                finally:
                    resume_worker(target_group)
                    command(target, "./scripts/stop.sh", "--clean")
        finally:
            resume_worker(group)
