import hashlib
import json
import re
from dataclasses import asdict, dataclass
from uuid import UUID

from garimpei.domain.inference.condition_evidence import (
    PROMPT as CONDITION_PROMPT,
)
from garimpei.domain.inference.condition_evidence import (
    SCHEMA as CONDITION_SCHEMA,
)
from garimpei.domain.inference.condition_evidence import (
    VERSION as CONDITION_VERSION,
)
from garimpei.domain.inference.errors import InferenceError

VERSION = "local-evidence-v1"
MODEL = "qwen3.5:4b-q4_K_M"
SUPPORTED_PROFILES = frozenset({VERSION, CONDITION_VERSION})


@dataclass(frozen=True)
class ImageReference:
    id: str
    revision: int
    sha256: str

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[a-zA-Z0-9_-]{1,100}", self.id):
            raise InferenceError("invalid_image_identity")
        if self.revision < 1 or not re.fullmatch(r"[a-f0-9]{64}", self.sha256):
            raise InferenceError("invalid_image_revision_or_hash")


@dataclass(frozen=True)
class AnalysisInput:
    observation_id: UUID
    revision: int
    text: str
    images: tuple[ImageReference, ...]
    prompt_version: str = VERSION
    schema_version: str = VERSION
    cohort_id: UUID | None = None
    cohort_generation: int | None = None

    def __post_init__(self) -> None:
        if self.revision < 1 or len(self.text.encode()) > 16384 or len(self.images) > 4:
            raise InferenceError("capacity_limit")
        if len({image.id for image in self.images}) != len(self.images):
            raise InferenceError("duplicate_image_identity")
        if not self.text.strip() and not self.images:
            raise InferenceError("insufficient_input")
        if (
            self.prompt_version not in SUPPORTED_PROFILES
            or self.schema_version != self.prompt_version
        ):
            raise InferenceError("unsupported_prompt_or_schema")
        grouped = (
            self.cohort_id is not None
            and self.cohort_generation is not None
            and self.cohort_generation > 0
        )
        if self.prompt_version == CONDITION_VERSION and not grouped:
            raise InferenceError("condition_cohort_required")
        if self.prompt_version == VERSION and (
            self.cohort_id is not None or self.cohort_generation is not None
        ):
            raise InferenceError("unsupported_cohort")

    def signature(self, artifact: str) -> str:
        data = asdict(self) | {
            "artifact": artifact,
            "transformation": "512-v1",
            "options": {
                "num_ctx": 4096,
                "num_predict": 512,
                "temperature": 0,
                "think": False,
                "visual_text": False,
            },
        }
        if self.cohort_id is None:
            data.pop("cohort_id", None)
            data.pop("cohort_generation", None)
        if self.prompt_version == CONDITION_VERSION:
            data["condition_profile"] = hashlib.sha256(
                (CONDITION_PROMPT + json.dumps(CONDITION_SCHEMA, sort_keys=True)).encode()
            ).hexdigest()
        return hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()
