from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import pytest

from tests.factories.runtime import (
    FoundationInstance,
    pause_worker,
    prepare_instance,
    resume_worker,
)


@pytest.fixture(scope="module")
def robot_instance(tmp_path_factory: pytest.TempPathFactory) -> Iterator[FoundationInstance]:
    root = Path(__file__).resolve().parents[4]
    instance = prepare_instance(root, tmp_path_factory.mktemp("robot"), "f22_" + uuid4().hex[:8])
    start = instance.command("./scripts/init.sh", "--disposable")
    assert start.returncode == 0, start.stdout + start.stderr
    try:
        yield instance
    finally:
        stop = instance.command("./scripts/stop.sh", "--clean")
        assert stop.returncode == 0, stop.stdout + stop.stderr


@pytest.mark.parametrize(
    "case", ["admission_cases", "concurrent_cases", "failure_cases", "inference_cases"]
)
def test_persistent_robot_boundaries(robot_instance: FoundationInstance, case: str) -> None:
    group = pause_worker(robot_instance)
    try:
        result = robot_instance.shell(
            f"from tests.factories.robot import {case}; {case}(); print('ROBOT_CASE_PASS:{case}')"
        )
        assert result.returncode == 0, result.stdout + result.stderr
    finally:
        resume_worker(group)
