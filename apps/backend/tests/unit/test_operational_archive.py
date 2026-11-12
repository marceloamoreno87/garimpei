import io
import tarfile
from pathlib import Path

import pytest

from garimpei.infra.gateway.operations.archive_gateway import ArchiveGateway, ArchiveInvalid


def test_archive_validates_hashes_and_never_extracts_untrusted_paths(tmp_path: Path) -> None:
    gateway = ArchiveGateway(tmp_path, reserve_bytes=0, budget_bytes=1024 * 1024)
    data = b'{"model":"synthetic","pk":"1","fields":{}}\n'
    path = gateway.write(
        "completed",
        "00000000-0000-4000-8000-000000000017",
        {"format_version": 1},
        {"records.jsonl": data},
    )
    manifest, files = gateway.read(path)
    assert files == {"records.jsonl": data}
    assert manifest["format_version"] == 1
    unsafe = tmp_path / "unsafe.tar.gz"
    with tarfile.open(unsafe, "w:gz") as archive:
        info = tarfile.TarInfo("../outside")
        info.size = 1
        archive.addfile(info, io.BytesIO(b"x"))
    with pytest.raises(ArchiveInvalid):
        gateway.read(unsafe)
    assert not (tmp_path.parent / "outside").exists()


def test_failed_publication_preserves_previous_complete_archive(tmp_path: Path) -> None:
    gateway = ArchiveGateway(tmp_path, reserve_bytes=0, budget_bytes=1024 * 1024)
    prior = gateway.write(
        "completed",
        "00000000-0000-4000-8000-000000000017",
        {"format_version": 1},
        {"records.jsonl": b"{}\n"},
    )
    original = prior.read_bytes()
    gateway = ArchiveGateway(tmp_path, reserve_bytes=0, budget_bytes=1)
    with pytest.raises(ArchiveInvalid):
        gateway.write(
            "completed",
            "00000000-0000-4000-8000-000000000018",
            {"format_version": 1},
            {"records.jsonl": b"{}\n"},
        )
    assert prior.read_bytes() == original


@pytest.mark.parametrize(
    "payload",
    [
        {"content": {"cookies": [{"name": "synthetic-canary"}]}},
        {"image": "https://example.test/photo?access_token=synthetic-canary"},
        {"url": "https://username:synthetic-canary@example.test/photo"},
    ],
)
def test_json_does_not_authorize_archiving_private_credentials(payload: object) -> None:
    from garimpei.infra.gateway.operations.private_fields import validate_private_fields

    with pytest.raises(ArchiveInvalid):
        validate_private_fields(payload)


def test_signed_media_access_is_excluded_while_version_and_hash_remain() -> None:
    from garimpei.infra.gateway.operations.private_fields import (
        sanitize_transient_media,
        validate_private_fields,
    )

    observation = {
        "evidence": {
            "image_url": "https://scontent.example.test/photo.jpg?oh=synthetic-canary&oe=tomorrow"
        },
        "media_version": "version-A",
        "sha256": "a" * 64,
    }
    sanitized = sanitize_transient_media(observation)
    validate_private_fields(sanitized)
    assert sanitized == {
        "evidence": {"image_url": "https://scontent.example.test/photo.jpg"},
        "media_version": "version-A",
        "sha256": "a" * 64,
    }
    assert "synthetic-canary" not in str(sanitized)
