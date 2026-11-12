import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import NotRequired, TypedDict, cast

import pytest


class NegativeCase(TypedDict):
    name: str
    files: dict[str, str]
    commands: list[list[str]]
    expected: str
    dependency: NotRequired[str]


BACKEND = Path(__file__).resolve().parents[2]
ROOT = BACKEND.parents[1]
CASES = cast(
    list[NegativeCase],
    json.loads((BACKEND / "tests/fixtures/foundation/cases.json").read_text())["gates"],
)


@pytest.mark.parametrize("case", CASES, ids=[case["name"] for case in CASES])
def test_gate_and_canonical_entry_reject_violation(tmp_path: Path, case: NegativeCase) -> None:
    copy = tmp_path / "backend"
    shutil.copytree(
        BACKEND,
        copy,
        ignore=shutil.ignore_patterns(
            ".venv",
            "__pycache__",
            ".mypy_cache",
            ".ruff_cache",
            ".pytest_cache",
            ".import_linter_cache",
            ".cache",
            "dist",
        ),
    )
    (copy / ".venv").symlink_to(BACKEND / ".venv", target_is_directory=True)
    for path, content in case["files"].items():
        (copy / path).write_text(content)
    if "dependency" in case:
        pyproject = copy / "pyproject.toml"
        pyproject.write_text(
            pyproject.read_text().replace(
                "dependencies = [", f'dependencies = ["{case["dependency"]}",', 1
            )
        )
    environment = dict(
        os.environ,
        PYTHONPATH=str(copy / "src"),
        DJANGO_SETTINGS_MODULE="garimpei.config.test_settings",
    )
    for command in case["commands"]:
        result = subprocess.run(
            ["uv", "run", "--frozen", "--no-sync", *command],
            cwd=copy,
            env=environment,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode != 0, (case["name"], result.stdout, result.stderr)
        assert case["expected"].lower() in (result.stdout + result.stderr).lower()
        save_negative_evidence(case["name"], command, result)
    result = subprocess.run(
        ["node", str(ROOT / "scripts/run-gates.mjs"), f"--cwd={copy}"],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode != 0
    assert "Six Python groups approved" not in result.stdout
    save_negative_evidence(case["name"] + "-canonical", ["node", "scripts/run-gates.mjs"], result)


def save_negative_evidence(
    name: str, command: list[str], result: subprocess.CompletedProcess[str]
) -> None:
    directory = os.environ.get("GARIMPEI_EVIDENCE_DIR")
    if directory:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        (path / f"negative-{name}.json").write_text(
            json.dumps(
                {
                    "command": command,
                    "exit": result.returncode,
                    "stdout": result.stdout[-10000:],
                    "stderr": result.stderr[-10000:],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n"
        )


def test_missing_gate_source_is_precondition_failure(tmp_path: Path) -> None:
    copy = tmp_path / "backend"
    shutil.copytree(
        BACKEND,
        copy,
        ignore=shutil.ignore_patterns(
            ".venv",
            "__pycache__",
            ".mypy_cache",
            ".pytest_cache",
            ".import_linter_cache",
            ".cache",
            "dist",
        ),
    )
    (copy / ".venv").symlink_to(BACKEND / ".venv", target_is_directory=True)
    (copy / "scripts/quality/check_cycles.py").unlink()
    result = subprocess.run(
        ["node", str(ROOT / "scripts/run-gates.mjs"), f"--cwd={copy}"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 64
    assert "check_cycles.py" in result.stderr
    assert "PASS" not in result.stdout
