import io
import json
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


@pytest.mark.parametrize("corruption", ["truncated", "hash", "version", "duplicate", "symlink"])
def test_archive_rejects_isolated_corruptions(tmp_path: Path, corruption: str) -> None:
    gateway = ArchiveGateway(tmp_path, reserve_bytes=0, budget_bytes=1024 * 1024)
    path = gateway.write(
        "completed",
        "00000000-0000-4000-8000-000000000017",
        {"format_version": 1},
        {"records.jsonl": b"{}\n"},
    )
    manifest, files = gateway.read(path)
    damaged = tmp_path / "damaged.tar.gz"
    if corruption == "truncated":
        damaged.write_bytes(path.read_bytes()[:40])
    else:
        if corruption == "version":
            manifest["format_version"] = 999
        if corruption == "hash":
            files["records.jsonl"] = b"altered"
        with tarfile.open(damaged, "w:gz") as archive:
            for name, data in files.items():
                member = tarfile.TarInfo(name)
                member.size = len(data)
                archive.addfile(member, io.BytesIO(data))
                if corruption == "duplicate":
                    archive.addfile(member, io.BytesIO(data))
            data = json.dumps(manifest).encode()
            member = tarfile.TarInfo("manifest.json")
            member.size = len(data)
            archive.addfile(member, io.BytesIO(data))
            if corruption == "symlink":
                member = tarfile.TarInfo("link.jsonl")
                member.type, member.linkname = tarfile.SYMTYPE, "../outside"
                archive.addfile(member)
    with pytest.raises(ArchiveInvalid):
        gateway.read(damaged)
    assert not (tmp_path.parent / "outside").exists()
    assert gateway.read(path)[1] == {"records.jsonl": b"{}\n"}


def test_interrupted_export_keeps_exact_source_and_removes_partial(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from garimpei.infra.gateway.operations.archive_gateway import copy_archive

    gateway = ArchiveGateway(tmp_path, reserve_bytes=0, budget_bytes=1024 * 1024)
    path = gateway.write(
        "completed",
        "00000000-0000-4000-8000-000000000017",
        {"format_version": 1},
        {"records.jsonl": b"{}\n"},
    )
    before = path.read_bytes()

    def interrupt(reader: io.BufferedReader, output: io.BufferedWriter, started: float) -> None:
        output.write(reader.read(16))
        raise OSError("controlled interrupted export")

    monkeypatch.setattr("garimpei.infra.gateway.operations.archive_gateway._copy_bytes", interrupt)
    with pytest.raises(OSError):
        copy_archive(gateway, path, "00000000-0000-4000-8000-000000000018")
    assert path.read_bytes() == before
    assert not tuple((tmp_path / "exports").iterdir())
    assert not tuple((tmp_path / "partial").iterdir())
