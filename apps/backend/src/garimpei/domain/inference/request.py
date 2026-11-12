import hashlib
import json
import re
from dataclasses import asdict, dataclass
from uuid import UUID

from garimpei.domain.inference.errors import InferenceError

VERSION = "local-evidence-v1"
MODEL = "qwen3.5:4b-q4_K_M"


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

    def __post_init__(self) -> None:
        if self.revision < 1 or len(self.text.encode()) > 16384 or len(self.images) > 4:
            raise InferenceError("capacity_limit")
        if len({image.id for image in self.images}) != len(self.images):
            raise InferenceError("duplicate_image_identity")
        if not self.text.strip() and not self.images:
            raise InferenceError("insufficient_input")
        if self.prompt_version != VERSION or self.schema_version != VERSION:
            raise InferenceError("unsupported_prompt_or_schema")

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
        return hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()
