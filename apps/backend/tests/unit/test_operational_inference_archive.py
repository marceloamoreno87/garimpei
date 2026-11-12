import hashlib
import io
import json
from pathlib import Path

import pytest
from PIL import Image

from garimpei.infra.gateway.operations.archive_gateway import ArchiveInvalid
from garimpei.infra.gateway.operations.inference_archive_gateway import InferenceArchiveGateway


def _prepared_input() -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (4, 4), "green").save(output, format="PNG")
    return output.getvalue()


def _tables(identity: str) -> dict[str, bytes]:
    row = {"fields": {"content": {"image_hash": identity}}}
    return {"runtime.inferencepart.jsonl": (json.dumps(row) + "\n").encode()}


def test_prepared_input_restores_exact_bytes_without_copying_private_directory(
    tmp_path: Path,
) -> None:
    source, target = tmp_path / "source", tmp_path / "target"
    source.mkdir()
    data = _prepared_input()
    identity = hashlib.sha256(data).hexdigest()
    (source / identity).write_bytes(data)
    (source / "model-lock.json").write_text("synthetic-private-canary")
    (source / ".env").write_text("synthetic-private-canary")
    files, metadata = InferenceArchiveGateway(source).capture(_tables(identity))
    assert set(files) == {f"inference/{identity}"}
    assert all(b"synthetic-private-canary" not in value for value in files.values())
    InferenceArchiveGateway(target).restore(metadata, _tables(identity) | files)
    assert (target / identity).read_bytes() == data
    assert (target / identity).stat().st_mode & 0o777 == 0o600
    assert target.stat().st_mode & 0o777 == 0o700
    assert not (target / "model-lock.json").exists()


def test_missing_prepared_input_cannot_be_advertised_as_complete(tmp_path: Path) -> None:
    identity = hashlib.sha256(_prepared_input()).hexdigest()
    with pytest.raises(ArchiveInvalid, match="inference_input_missing"):
        InferenceArchiveGateway(tmp_path).capture(_tables(identity))
    with pytest.raises(ArchiveInvalid, match="inference_input_coverage_incomplete"):
        InferenceArchiveGateway(tmp_path).validate({}, _tables(identity))


@pytest.mark.parametrize("identity", ["../private", "https://example.invalid/private", "z" * 64])
def test_prepared_image_reference_never_becomes_an_arbitrary_file_path(
    tmp_path: Path, identity: str
) -> None:
    with pytest.raises(ArchiveInvalid, match="inference_input_invalid"):
        InferenceArchiveGateway(tmp_path).capture(_tables(identity))
