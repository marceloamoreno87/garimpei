import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest

from tests.factories.runtime import FoundationInstance, prepare_instance


@pytest.fixture(scope="session")
def foundations(tmp_path_factory: pytest.TempPathFactory) -> Iterator[list[FoundationInstance]]:
    root = Path(__file__).resolve().parents[3]
    private = tmp_path_factory.mktemp("foundation")
    token = uuid.uuid4().hex[:8]
    instances = [prepare_instance(root, private, f"test_{token}_{letter}") for letter in ("a", "b")]
    started: list[FoundationInstance] = []
    try:
        for instance in instances:
            result = instance.command("./scripts/init.sh", "--disposable")
            assert result.returncode == 0, result.stdout + result.stderr
            started.append(instance)
        yield instances
    finally:
        for instance in started:
            result = instance.command("./scripts/stop.sh", "--clean")
            assert result.returncode == 0, result.stdout + result.stderr
