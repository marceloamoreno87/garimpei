import subprocess
from pathlib import Path

import pytest

from garimpei.config.env import ConfigurationError, load_alert_settings, load_config


def test_missing_secret_identifies_key_without_echo(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="DJANGO_SECRET_KEY"):
        load_config({}, root=tmp_path)


def test_real_engine_canonical_lid_can_be_the_verified_direct_destination(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GARIMPEI_WAHA_RECIPIENT", "123456789@lid")
    monkeypatch.setenv("DJANGO_SECRET_KEY", "synthetic-test-key")
    monkeypatch.setenv("POSTGRES_PASSWORD", "synthetic-test-key")
    monkeypatch.setenv("WAHA_API_KEY", "synthetic-test-key")
    assert load_alert_settings().recipient == "123456789@lid"


def test_invalid_port_identifies_non_secret_value(tmp_path: Path) -> None:
    values = {
        "DJANGO_SECRET_KEY": "private-django-canary",
        "POSTGRES_PASSWORD": "private-postgres-canary",
        "WAHA_API_KEY": "private-waha-canary",
        "GARIMPEI_WEB_PORT": "oops",
    }
    with pytest.raises(ConfigurationError, match="oops") as error:
        load_config(values, root=tmp_path)
    assert "canary" not in str(error.value)


def test_eval_requires_explicit_identity(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="GARIMPEI_INSTANCE"):
        load_config({"GARIMPEI_ENV": "eval"}, root=tmp_path, require_secrets=False)


def test_file_is_data_and_explicit_environment_wins(tmp_path: Path) -> None:
    private = tmp_path / "private.env"
    private.write_text("LOG_LEVEL=DEBUG\nEXTRA=$(touch never-execute)\n")
    config = load_config(
        {"GARIMPEI_ENV_FILE": str(private), "LOG_LEVEL": "WARNING"},
        root=tmp_path,
        require_secrets=False,
    )
    assert config.log_level == "WARNING"
    assert "EXTRA=$(touch never-execute)" in private.read_text()
    assert not (tmp_path / "never-execute").exists()


def test_unborn_normalized_branch_names_still_have_distinct_stable_identity(tmp_path: Path) -> None:
    assert (
        subprocess.run(
            ["git", "init", "--quiet", "--initial-branch=topic-a", str(tmp_path)]
        ).returncode
        == 0
    )
    first = load_config({}, root=tmp_path, require_secrets=False)
    assert (
        subprocess.run(
            ["git", "-C", str(tmp_path), "symbolic-ref", "HEAD", "refs/heads/topic_a"]
        ).returncode
        == 0
    )
    second = load_config({}, root=tmp_path, require_secrets=False)
    assert first.instance != second.instance
    assert second == load_config({}, root=tmp_path, require_secrets=False)
    assert first.database.startswith("garimpei_")
