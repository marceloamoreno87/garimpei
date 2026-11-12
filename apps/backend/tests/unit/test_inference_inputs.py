import hashlib
import json
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

import pytest
from PIL import Image
from tokenizers import Tokenizer, models, pre_tokenizers

from garimpei.domain.inference.errors import InferenceError
from garimpei.domain.inference.request import AnalysisInput, ImageReference
from garimpei.infra.gateway.inference.input_preparer import LocalInputPreparer
from garimpei.infra.gateway.inference.quota import REQUEST_RESERVATION, LocalQuota
from garimpei.infra.gateway.inference.registry import register_file
from tests.factories.inference import inference_settings


def prepared(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> LocalInputPreparer:
    settings = inference_settings(tmp_path, "http://127.0.0.1:1")
    codec = Tokenizer(models.WordLevel({"[UNK]": 0, "console": 1}, unk_token="[UNK]"))
    codec.pre_tokenizer = pre_tokenizers.Whitespace()
    codec.save(str(settings.tokenizer))
    lock = json.loads(settings.model_lock.read_text())
    lock["visual_context_verified"] = True
    lock["tokenizer"]["sha256"] = hashlib.sha256(settings.tokenizer.read_bytes()).hexdigest()
    settings.model_lock.write_text(json.dumps(lock))

    def synthetic_tokenizer_lock(path: Path) -> dict[str, object]:
        # These input tests replace the tokenizer I/O; artifact-policy tests verify official pins.
        return dict(json.loads(path.read_text()))

    monkeypatch.setattr(
        "garimpei.infra.gateway.inference.input_preparer.read_lock", synthetic_tokenizer_lock
    )
    return LocalInputPreparer(settings)


def test_context_budget_and_unicode_are_checked_before_dispatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    preparer = prepared(tmp_path, monkeypatch)
    assert preparer.prepare(AnalysisInput(uuid4(), 1, "Câmera íntegra 日本語 🔍", ()))[0].text
    with pytest.raises(InferenceError, match="context_unverified"):
        preparer.prepare(AnalysisInput(uuid4(), 1, "console " * 2000, ()))


def test_registered_image_is_versioned_and_original_is_not_modified(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    preparer = prepared(tmp_path, monkeypatch)
    settings = preparer._settings
    photo = tmp_path / "original.png"
    Image.new("RGB", (1000, 500), "red").save(photo)
    raw = photo.read_bytes()
    reference = register_file(
        settings,
        photo,
        {
            "id": "test-photo",
            "revision": 1,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "authorization": "Synthetic test fixture",
        },
    )
    parts = preparer.prepare(AnalysisInput(uuid4(), 1, "", (reference,)))
    assert photo.read_bytes() == raw
    digest = parts[0].image_hash
    assert digest is not None
    with Image.open(settings.directory / digest) as derivative:
        assert derivative.size == (512, 256)
    with pytest.raises(InferenceError, match="image_revision_mismatch"):
        preparer.prepare(
            AnalysisInput(uuid4(), 1, "", (ImageReference(reference.id, 2, reference.sha256),))
        )


def test_disk_reservations_are_atomic_idempotent_and_conservative(tmp_path: Path) -> None:
    settings = replace(
        inference_settings(tmp_path, "http://127.0.0.1:1"), disk_limit=REQUEST_RESERVATION + 4096
    )
    quota = LocalQuota(settings)
    quota.reserve("a" * 64)
    quota.reserve("a" * 64)
    with pytest.raises(InferenceError, match="capacity_limit"):
        quota.reserve("b" * 64)
    assert json.loads((tmp_path / "admission-reservations.json").read_text()) == ["a" * 64]


def test_nonsemantic_measurements_do_not_invalidate_cached_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    preparer = prepared(tmp_path, monkeypatch)
    before = preparer.artifact()
    lock = json.loads(preparer._settings.model_lock.read_text())
    lock["visual_profile"] = {"metrics": {"total_duration": 1000000}}
    preparer._settings.model_lock.write_text(json.dumps(lock))
    assert preparer.artifact() == before
