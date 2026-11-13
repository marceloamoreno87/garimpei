"""Process boundary keeps Django/runtime credentials out of the pytest host."""

import json
import os
import subprocess
from pathlib import Path
from typing import IO, cast


class GoldDriver:
    def __init__(self, private: Path) -> None:
        self.root = Path(__file__).parents[4]
        self._log: IO[str] = (private / "gold-lab-stderr.txt").open("w")
        self.process = subprocess.Popen(
            [
                "uv",
                "run",
                "--project",
                "apps/backend",
                "--frozen",
                "--no-sync",
                "python",
                "-m",
                "tests.factories.gold_lab",
            ],
            cwd=self.root,
            env=dict(os.environ, PYTHONPATH=str(self.root / "apps/backend")),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=self._log,
            text=True,
        )
        self.ready = self._read()

    def _read(self) -> dict[str, object]:
        assert self.process.stdout is not None
        for line in self.process.stdout:
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if value.get("ready") or value.get("state") == "error":
                assert value.get("state") != "error", value
                return cast(dict[str, object], value)
        raise AssertionError(f"F21 lab ended unexpectedly: {self.process.poll()}")

    def action(self, action: str, **payload: object) -> dict[str, object]:
        assert self.process.stdin is not None
        self.process.stdin.write(json.dumps(dict(action=action, **payload)) + "\n")
        self.process.stdin.flush()
        return self._read()

    def shell(self, code: str) -> str:
        result = subprocess.run(
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
            cwd=self.root,
            env=dict(
                os.environ,
                GARIMPEI_ENV_FILE=str(self.ready["private_file"]),
                DJANGO_SETTINGS_MODULE="garimpei.config.settings",
            ),
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        return result.stdout

    def close(self) -> None:
        if self.process.stdin and self.process.poll() is None:
            self.process.stdin.write('{"action":"quit"}\n')
            self.process.stdin.flush()
            self.process.wait(timeout=120)
        self._log.close()
