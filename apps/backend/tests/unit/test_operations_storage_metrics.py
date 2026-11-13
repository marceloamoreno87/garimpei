from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import TracebackType

import pytest

from tests.factories.operations_storage_metrics import read_storage_metrics
from tests.factories.runtime import FoundationInstance

NOW = datetime(2026, 11, 13, tzinfo=UTC)


class QueueDatabase:
    def __init__(self, since: datetime | None) -> None:
        self.since = since

    def __enter__(self) -> "QueueDatabase":
        return self

    def __exit__(
        self,
        kind: type[BaseException] | None,
        value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        pass

    def execute(self, query: str) -> "QueueDatabase":
        assert query.lstrip().startswith("SELECT")
        return self

    def fetchone(self) -> tuple[datetime, datetime | None]:
        return NOW, self.since


def instance_with_storage(tmp_path: Path) -> FoundationInstance:
    (tmp_path / "checkout").mkdir()
    private = tmp_path / "owned.env"
    private.write_text(
        "GARIMPEI_ENV=eval\nGARIMPEI_INSTANCE=storage_metrics\n"
        "DJANGO_SECRET_KEY=synthetic\nPOSTGRES_PASSWORD=synthetic\nWAHA_API_KEY=synthetic\n"
        f"GARIMPEI_MEDIA_ROOT={tmp_path / 'media'}\n"
        f"GARIMPEI_BACKUP_DIR={tmp_path / 'backups'}\n"
    )
    return FoundationInstance(tmp_path / "checkout", private)


def database_with_age(monkeypatch: pytest.MonkeyPatch, since: datetime | None) -> None:
    def connect(*args: object, **kwargs: object) -> QueueDatabase:
        return QueueDatabase(since)

    monkeypatch.setattr("tests.factories.operations_storage_metrics.psycopg.connect", connect)


def write_bytes(path: Path, count: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * count)


def test_owned_storage_includes_external_media_exports_and_partial_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    instance = instance_with_storage(tmp_path)
    database_with_age(monkeypatch, NOW - timedelta(seconds=75))
    write_bytes(instance.config.directory / "web.log", 11)
    write_bytes(tmp_path / "media" / "originals" / "photo", 23)
    write_bytes(tmp_path / "backups" / "completed" / "one.tar.gz", 31)
    write_bytes(tmp_path / "backups" / "partial" / "next.tar.gz", 37)
    write_bytes(tmp_path / "backups" / "exports" / "one.tar.gz", 41)
    foreign = tmp_path / "foreign"
    write_bytes(foreign / "private", 997)
    (tmp_path / "media" / "foreign-dir").symlink_to(foreign, target_is_directory=True)
    (tmp_path / "media" / "foreign-file").symlink_to(foreign / "private")
    monkeypatch.setenv("GARIMPEI_MEDIA_ROOT", str(foreign))
    monkeypatch.setenv("GARIMPEI_BACKUP_DIR", str(foreign))
    assert read_storage_metrics(instance) == {
        "runtime_bytes": 11,
        "media_bytes": 23,
        "backup_bytes": 109,
        "oldest_pending_age_seconds": 75,
    }


@pytest.mark.parametrize("since", [None, NOW + timedelta(seconds=60)])
def test_absent_storage_and_empty_or_future_queue_have_no_negative_age(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, since: datetime | None
) -> None:
    instance = instance_with_storage(tmp_path)
    database_with_age(monkeypatch, since)
    assert set(read_storage_metrics(instance).values()) == {0}


def test_sampler_rejects_symlinked_storage_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    instance = instance_with_storage(tmp_path)
    database_with_age(monkeypatch, NOW)
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    (tmp_path / "media").symlink_to(foreign, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        read_storage_metrics(instance)


def test_sampler_requires_eval_instance(tmp_path: Path) -> None:
    instance = instance_with_storage(tmp_path)
    instance.private_file.write_text(
        instance.private_file.read_text().replace("GARIMPEI_ENV=eval", "GARIMPEI_ENV=dev")
    )
    with pytest.raises(ValueError, match="eval"):
        read_storage_metrics(instance)


def test_sampler_rejects_symlinked_parent_of_storage_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    instance = instance_with_storage(tmp_path)
    database_with_age(monkeypatch, NOW)
    foreign = tmp_path / "foreign"
    write_bytes(foreign / "photos" / "private", 997)
    (tmp_path / "indirect").symlink_to(foreign, target_is_directory=True)
    with instance.private_file.open("a") as output:
        output.write(f"GARIMPEI_MEDIA_ROOT={tmp_path / 'indirect' / 'photos'}\n")
    with pytest.raises(ValueError, match="symlink"):
        read_storage_metrics(instance)
