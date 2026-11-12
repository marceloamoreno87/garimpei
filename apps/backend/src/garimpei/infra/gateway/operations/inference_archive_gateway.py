"""Only prepared F19 PNG inputs are copied, never model files, profiles or registry folders."""

import hashlib
import io
import json
import os
import re
import tempfile
from pathlib import Path

from PIL import Image

from garimpei.infra.gateway.operations.archive_gateway import ArchiveInvalid


class InferenceArchiveGateway:
    def __init__(self, directory: Path) -> None:
        self._directory = directory

    def capture(self, tables: dict[str, bytes]) -> tuple[dict[str, bytes], dict[str, object]]:
        identities = _required_images(tables)
        files = {}
        for identity in identities:
            path = self._directory / identity
            if self._directory.is_symlink() or path.is_symlink() or not path.is_file():
                raise ArchiveInvalid("inference_input_missing")
            if path.stat().st_size > 10485760:
                raise ArchiveInvalid("inference_input_limit")
            data = path.read_bytes()
            _validate_image(identity, data)
            files[f"inference/{identity}"] = data
        return files, {"prepared_inference_images": sorted(identities)}

    def validate(self, metadata: dict[str, object], files: dict[str, bytes]) -> None:
        required = _required_images(files)
        declared = metadata.get("prepared_inference_images", [])
        expected = {f"inference/{identity}" for identity in required}
        if (
            declared != sorted(required)
            or {n for n in files if n.startswith("inference/")} != expected
        ):
            raise ArchiveInvalid("inference_input_coverage_incomplete")
        for identity in required:
            _validate_image(identity, files[f"inference/{identity}"])

    def restore(self, metadata: dict[str, object], files: dict[str, bytes]) -> None:
        self.validate(metadata, files)
        for identity in _required_images(files):
            self._store(identity, files[f"inference/{identity}"])

    def _store(self, identity: str, data: bytes) -> None:
        if self._directory.is_symlink():
            raise ArchiveInvalid("inference_input_directory_invalid")
        self._directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self._directory.chmod(0o700)
        target = self._directory / identity
        if target.is_symlink():
            raise ArchiveInvalid("inference_input_directory_invalid")
        if target.exists():
            if target.stat().st_size > 10485760:
                raise ArchiveInvalid("inference_input_limit")
            _validate_image(identity, target.read_bytes())
            return
        descriptor, name = tempfile.mkstemp(prefix=".restore-", dir=self._directory)
        temporary = Path(name)
        try:
            with os.fdopen(descriptor, "wb") as output:
                os.fchmod(output.fileno(), 0o600)
                output.write(data)
                output.flush()
                os.fsync(output.fileno())
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)


def _required_images(files: dict[str, bytes]) -> set[str]:
    result = set()
    for line in files["runtime.inferencepart.jsonl"].splitlines():
        content = json.loads(line)["fields"]["content"]
        if not isinstance(content, dict):
            raise ArchiveInvalid("inference_input_invalid")
        identity = content.get("image_hash")
        if identity is None:
            continue
        if not isinstance(identity, str) or re.fullmatch(r"[a-f0-9]{64}", identity) is None:
            raise ArchiveInvalid("inference_input_invalid")
        result.add(identity)
    return result


def _validate_image(identity: str, data: bytes) -> None:
    if len(data) > 10485760 or hashlib.sha256(data).hexdigest() != identity:
        raise ArchiveInvalid("inference_input_checksum_invalid")
    if not data.endswith(b"\x00\x00\x00\x00IEND\xaeB`\x82"):
        raise ArchiveInvalid("inference_input_format_invalid")
    try:
        with Image.open(io.BytesIO(data)) as image:
            _validate_shape(image)
            image.verify()
    except (OSError, ValueError, SyntaxError, Image.DecompressionBombError):
        raise ArchiveInvalid("inference_input_format_invalid") from None


def _validate_shape(image: Image.Image) -> None:
    if image.format != "PNG" or image.mode != "RGB" or image.info or max(image.size) > 512:
        raise ArchiveInvalid("inference_input_format_invalid")
