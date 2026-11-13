"""Exercise operational CLI commands on an exclusively owned, disposable F17 lab."""

import argparse
import io
import json
import tarfile
from pathlib import Path

from tests.factories.operations_lab import instances, lifecycle, prepare, seed
from tests.factories.runtime import FoundationInstance

SNAPSHOT = """
import json,hashlib
from django.apps import apps
names=['Listing','ListingObservation','ListingEvent','MonitoringConfiguration','ConditionAssessment','ManualCondition','ManualConditionHistory','AlertIntent','AlertAttempt']
rows={}
for name in names:
 try:model=apps.get_model('runtime',name)
 except LookupError:continue
 rows[name]=list(model.objects.order_by('pk').values())
print(json.dumps({'sha256':hashlib.sha256(json.dumps(rows,sort_keys=True,default=str).encode()).hexdigest(),'counts':{key:len(value) for key,value in rows.items()}}))
"""


def shell(instance: FoundationInstance, code: str) -> dict[str, object]:
    result = instance.shell(code)
    assert result.returncode == 0, "owned shell setup/inspection failed"
    return json.loads(result.stdout.strip().splitlines()[-1])


def invoke(
    instance: FoundationInstance, command: str, *arguments: str
) -> dict[str, object]:
    result = instance.command(
        "uv",
        "run",
        "--project",
        "apps/backend",
        "--frozen",
        "--no-sync",
        "python",
        "apps/backend/manage.py",
        command,
        *arguments,
    )
    return {"exit": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


def corruptions(archive: Path, directory: Path) -> list[Path]:
    with tarfile.open(archive, "r:gz") as reader:
        files = {
            member.name: reader.extractfile(member).read()
            for member in reader.getmembers()
        }
    outputs = []
    for case in ("truncated", "hash", "schema", "unsafe"):
        output = directory / (case + ".tar.gz")
        outputs.append(output)
        if case == "truncated":
            output.write_bytes(archive.read_bytes()[:40])
            continue
        changed = dict(files)
        if case == "hash":
            name = next(name for name in changed if name != "manifest.json")
            changed[name] += b"altered"
        if case == "schema":
            manifest = json.loads(changed["manifest.json"])
            manifest["schema_hash"] = "0" * 64
            changed["manifest.json"] = json.dumps(manifest).encode()
        if case == "unsafe":
            changed["../outside-cli-probe"] = b"unsafe"
        with tarfile.open(output, "w:gz") as writer:
            for name, content in changed.items():
                info = tarfile.TarInfo(name)
                info.size = len(content)
                writer.addfile(info, io.BytesIO(content))
    return outputs


def run(directory: Path) -> None:
    prepare(directory)
    results: dict[str, object] = {}
    try:
        lifecycle(directory, True)
        seed(directory, "backup")
        source, target = instances(directory)
        before = shell(source, SNAPSHOT)
        results["create"] = invoke(source, "operational_backup", "create")
        results["list"] = invoke(source, "operational_backup", "list")
        selected = shell(
            source,
            """
import json
from garimpei.main import build_backup_repository
from garimpei.infra.persistence.operations_models import BackupRecord
r=BackupRecord.objects.filter(kind='backup',state='completed').latest('finished_at')
print(json.dumps({'id':str(r.id),'archive':str(build_backup_repository()._archives.resolve(r.file_key)),'snapshot':r.snapshot_at.isoformat()}))
""",
        )
        results["verify"] = invoke(
            source, "operational_backup", "verify", "--id", str(selected["id"])
        )
        empty = shell(target, SNAPSHOT)
        rejected = []
        for archive in corruptions(Path(str(selected["archive"])), directory):
            response = invoke(
                target,
                "operational_backup",
                "restore",
                "--archive",
                str(archive),
                "--isolated",
            )
            assert response["exit"] != 0
            assert shell(target, SNAPSHOT) == empty
            assert not (directory.parent / "outside-cli-probe").exists()
            rejected.append(
                {
                    "case": archive.stem,
                    "exit": response["exit"],
                    "safe_reason": "operation_not_completed",
                }
            )
        results["corruptions"] = rejected
        results["without_isolated"] = invoke(
            target,
            "operational_backup",
            "restore",
            "--archive",
            str(selected["archive"]),
        )
        assert results["without_isolated"]["exit"] != 0
        assert shell(target, SNAPSHOT) == empty
        manifest_file = target.config.directory / "manifest.json"
        manifest_original = manifest_file.read_bytes()
        try:
            manifest = json.loads(manifest_original)
            manifest["disposable"] = False
            manifest_file.write_text(json.dumps(manifest))
            results["not_disposable"] = invoke(
                target,
                "operational_backup",
                "restore",
                "--archive",
                str(selected["archive"]),
                "--isolated",
            )
            assert results["not_disposable"]["exit"] != 0
        finally:
            manifest_file.write_bytes(manifest_original)
        private_original = target.private_file.read_bytes()
        try:
            with target.private_file.open("a") as output:
                output.write("GARIMPEI_ENV=dev\n")
            results["dev_target"] = invoke(
                target,
                "operational_backup",
                "restore",
                "--archive",
                str(selected["archive"]),
                "--isolated",
            )
            assert results["dev_target"]["exit"] != 0
        finally:
            target.private_file.write_bytes(private_original)
        assert shell(target, SNAPSHOT) == empty
        results["restore"] = invoke(
            target,
            "operational_backup",
            "restore",
            "--archive",
            str(selected["archive"]),
            "--isolated",
        )
        assert results["restore"]["exit"] == 0
        assert shell(target, SNAPSHOT) == before
        assert shell(source, SNAPSHOT) == before
        results["status"] = invoke(target, "operational_status")
        results["nonempty_target"] = invoke(
            target,
            "operational_backup",
            "restore",
            "--archive",
            str(selected["archive"]),
            "--isolated",
        )
        assert results["nonempty_target"]["exit"] != 0
        assert target.command("./scripts/stop.sh").returncode == 0
        assert target.command("./scripts/init.sh", "--disposable").returncode == 0
        results["status_after_restart"] = invoke(target, "operational_status")
        assert "Despacho bloqueado" in str(results["status_after_restart"]["stdout"])
        assert shell(source, SNAPSHOT) == before
        results["source_preserved"] = True
        results["business_counts"] = before["counts"]
        results["restore_output_has_snapshot"] = str(selected["snapshot"]) in str(
            results["restore"]["stdout"]
        )
        results["profile_confirmed"] = False
    finally:
        lifecycle(directory, False)
        # Do not export environment paths, credentials or archive payloads.
        (directory / "cli-results.json").write_text(
            json.dumps(results, indent=2) + "\n"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True, type=Path)
    run(parser.parse_args().directory.resolve())
