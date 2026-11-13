"""AI preparation must reject foreign Docker resources before any mutation."""

import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]


@pytest.mark.parametrize("resource", ["container", "volume", "network"])
def test_prepare_refuses_foreign_resource_before_compose_or_gpu_reservation(
    tmp_path: Path, resource: str
) -> None:
    shim = tmp_path / "docker"
    shim.write_text(
        """#!/bin/sh
case "$1:$2" in
 ps:*) [ "$FOREIGN_RESOURCE" != container ] || echo foreign-container;;
 container:inspect) echo '/another/checkout|eval_ownership_test';;
 volume:ls) [ "$FOREIGN_RESOURCE" != volume ] || echo garimpei-eval_ownership_test_ollama_models;;
 network:ls) [ "$FOREIGN_RESOURCE" != network ] || echo garimpei-eval_ownership_test_inference;;
 volume:inspect|network:inspect) echo '/another/checkout|eval_ownership_test';;
 compose:*)
  case "$*" in
   *" ps "*) [ "$FOREIGN_RESOURCE" != container ] || echo foreign-container;;
   *) echo MUTATION-ATTEMPTED >&2; exit 99;;
  esac;;
 *) echo MUTATION-ATTEMPTED >&2; exit 99;;
esac
exit 0
"""
    )
    shim.chmod(0o700)
    result = subprocess.run(
        ["bash", str(ROOT / "scripts/docker-ai.sh"), "prepare"],
        env=dict(
            os.environ,
            PATH=str(tmp_path) + ":" + os.environ["PATH"],
            FOREIGN_RESOURCE=resource,
            GARIMPEI_ENVIRONMENT_ID="eval_ownership_test",
            GARIMPEI_ENV_FILE=str(tmp_path / "synthetic.env"),
        ),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "ownership" in result.stderr.lower()
    assert "MUTATION-ATTEMPTED" not in result.stderr
