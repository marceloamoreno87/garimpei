"""The host adoption boundary refuses unsafe copies before mutating data."""

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SCRIPT = ROOT / "scripts/docker-adoption.sh"


def run_adoption(
    tmp_path: Path, docker_body: str, *arguments: str
) -> subprocess.CompletedProcess[str]:
    shim = tmp_path / "bin"
    shim.mkdir(exist_ok=True)
    docker = shim / "docker"
    docker.write_text("#!/bin/sh\n" + docker_body)
    docker.chmod(0o700)
    return subprocess.run(
        ["bash", str(SCRIPT), *arguments],
        env=dict(os.environ, PATH=str(shim) + ":" + os.environ["PATH"]),
        text=True,
        capture_output=True,
        check=False,
    )


def test_foreign_resource_is_refused_before_backup(tmp_path: Path) -> None:
    result = run_adoption(
        tmp_path,
        """
case "$1" in
ps) echo foreign;;
inspect) echo '/another/checkout|eval_foreign|postgres|true';;
*) echo 'mutation attempted' >&2; exit 99;;
esac
""",
        "snapshot", "garimpei-eval_foreign", str(tmp_path / "copy"),
    )
    assert result.returncode == 64
    assert "ownership" in result.stderr.lower()
    assert not (tmp_path / "copy").exists()


def test_running_automation_is_refused_before_dump(tmp_path: Path) -> None:
    result = run_adoption(
        tmp_path,
        f"""
case "$1" in
ps) echo active;;
inspect) echo '{ROOT}|eval_active|worker|true';;
*) echo 'mutation attempted' >&2; exit 99;;
esac
""",
        "snapshot", "garimpei-eval_active", str(tmp_path / "copy"),
    )
    assert result.returncode == 64
    assert "stopped" in result.stderr.lower()
    assert not (tmp_path / "copy").exists()


def database_docker(*, dump_exit: int) -> str:
    return f"""
case "$1" in
ps) echo pg;;
inspect)
 case "$3" in *Mounts*) exit 0;; *container*) echo 'container postgres sha256:synthetic';;
 *) echo '{ROOT}|eval_copy|postgres|true';; esac;;
exec)
 case "$3" in
 printenv) echo garimpei_eval_copy;;
 psql)
  for last in "$@"; do :; done
  case "$last" in
   *NOT*) echo t;; *"state='active'"*) echo 0;;
   *string_agg*) echo "SELECT 'runtime.robotcontrol' AS relation, 1 AS rows";;
   *) printf 'runtime.robotcontrol|1\\n';;
  esac;;
 pg_dump) echo synthetic-dump; exit {dump_exit};;
 esac;;
esac
"""


def test_failed_database_copy_does_not_publish_ready_marker(tmp_path: Path) -> None:
    result = run_adoption(
        tmp_path, database_docker(dump_exit=9),
        "snapshot", "garimpei-eval_copy", str(tmp_path / "copy"),
    )
    assert result.returncode == 9
    assert (tmp_path / "copy").is_dir()
    assert not (tmp_path / "copy/READY").exists()


def test_successful_database_snapshot_verifies_then_rejects_tamper(tmp_path: Path) -> None:
    folder = tmp_path / "copy"
    result = run_adoption(
        tmp_path, database_docker(dump_exit=0), "snapshot", "garimpei-eval_copy", str(folder)
    )
    assert result.returncode == 0, result.stderr
    assert (folder / "READY").exists()
    (folder / "database.dump").write_text("tampered")
    restored = run_adoption(
        tmp_path, "echo docker-must-not-run >&2; exit 99\n",
        "restore-check", "garimpei-eval_target", str(folder),
    )
    assert restored.returncode == 64
    assert "checksum mismatch" in restored.stderr
    assert "docker-must-not-run" not in restored.stderr


def test_incomplete_copy_is_rejected_before_docker(tmp_path: Path) -> None:
    folder = tmp_path / "copy"
    folder.mkdir()
    result = run_adoption(
        tmp_path, "echo docker-must-not-run >&2; exit 99\n",
        "restore-check", "garimpei-eval_target", str(folder),
    )
    assert result.returncode == 64
    assert "incomplete" in result.stderr
    assert "docker-must-not-run" not in result.stderr


def test_added_unverified_archive_is_rejected_before_restore(tmp_path: Path) -> None:
    folder = tmp_path / "copy"
    copied = run_adoption(
        tmp_path, database_docker(dump_exit=0), "snapshot", "garimpei-eval_copy", str(folder)
    )
    assert copied.returncode == 0, copied.stderr
    (folder / "private.tar").write_bytes(b"unverified private payload")
    restored = run_adoption(
        tmp_path, "echo docker-must-not-run >&2; exit 99\n",
        "restore-check", "garimpei-eval_target", str(folder),
    )
    assert restored.returncode == 64
    assert "archive checksum" in restored.stderr
    assert "docker-must-not-run" not in restored.stderr
