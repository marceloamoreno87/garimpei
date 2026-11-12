import json
import uuid
from pathlib import Path

from tests.factories.runtime import prepare_instance


def test_clean_removes_owned_network_and_preserves_foreign_network(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[4]
    token = uuid.uuid4().hex[:10]
    instance = prepare_instance(root, tmp_path, "network_" + token)
    network = f"garimpei-{instance.config.environment_id}_default"
    foreign = "garimpei-foreign-test-" + token
    assert (
        instance.command(
            "docker", "network", "create", "--label", "com.garimpei.test_owner=" + token, foreign
        ).returncode
        == 0
    )
    try:
        result = instance.command("./scripts/init.sh", "--disposable")
        assert result.returncode == 0, result.stdout + result.stderr
        assert instance.command("./scripts/stop.sh", "--clean").returncode == 0
        assert instance.command("docker", "network", "inspect", network).returncode != 0
        assert instance.command("docker", "network", "inspect", foreign).returncode == 0
    finally:
        for name in [network, foreign]:
            inspect = instance.command("docker", "network", "inspect", name)
            if inspect.returncode == 0:
                data = json.loads(inspect.stdout)[0]
                assert not data["Containers"]
                assert data["Labels"].get("com.garimpei.test_owner") == token or data["Labels"].get(
                    "com.docker.compose.project"
                ) == network.removesuffix("_default")
                assert instance.command("docker", "network", "rm", name).returncode == 0
