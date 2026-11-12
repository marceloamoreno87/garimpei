from typing import cast

from garimpei.config.env import load_inference_settings
from garimpei.domain.inference.errors import InferenceError
from garimpei.domain.listing.assessment_policy import POLICY_VERSION
from garimpei.domain.media.media import MediaGallery
from garimpei.infra.gateway.inference.input_preparer import read_lock
from garimpei.infra.persistence.assessment_models import ConditionAssessment


def model_revision() -> str:
    try:
        return str(read_lock(load_inference_settings().model_lock)["model_digest"])
    except InferenceError:
        return ""


def applicable(row: ConditionAssessment, gallery: MediaGallery, model: str) -> bool:
    old = row.input_snapshot
    photos = cast(list[dict[str, object]], old["photos"])
    original = [(p["sha256"], p["state"]) for p in photos]
    current = [(p.sha256, p.state) for p in gallery.photos]
    text = (
        {key: row.listing.latest.evidence.get(key) for key in ["title", "description", "condition"]}
        if row.listing.latest
        else {}
    )
    return bool(
        row.model_revision == model
        and row.policy_version == POLICY_VERSION
        and old["text"] == text
        and row.observation_id == row.listing.latest_id
        and original == current
        and old["complete"] == gallery.complete
        and old["presence"] == gallery.presence
    )
