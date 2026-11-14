import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from uuid import UUID

from garimpei.domain.assistance.review import (
    ASSISTANCE_PROFILES,
    assistance_prompt,
    assistance_schema,
)
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
from garimpei.domain.inference.profile_limits import CONTEXT_TOKENS, output_token_limit

VERSION = "local-evidence-v1"
MODEL = "qwen3.5:4b-q4_K_M"
SUPPORTED_PROFILES = frozenset({VERSION, CONDITION_VERSION}) | ASSISTANCE_PROFILES


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
    observation_id: UUID | None
    revision: int
    text: str
    images: tuple[ImageReference, ...]
    prompt_version: str = VERSION
    schema_version: str = VERSION
    cohort_id: UUID | None = None
    cohort_generation: int | None = None
    target_kind: str = "listing_observation"
    target_id: UUID | None = None
    target_revision: int | None = None
    context: dict[str, object] = field(default_factory=dict)

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
        self._validate_target()
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

    def _validate_target(self) -> None:
        if self.prompt_version not in ASSISTANCE_PROFILES:
            if (
                self.observation_id is None
                or self.target_id is not None
                or self.context
                or self.target_kind != "listing_observation"
                or self.target_revision is not None
            ):
                raise InferenceError("observation_required")
            return
        if self.target_id is None or self.target_revision is None or self.target_revision < 1:
            raise InferenceError("typed_target_required")
        allowed = {"listing_observation"}
        if self.prompt_version == "investigation-support-v1":
            allowed.add("interest")
        if self.prompt_version == "operations-support-v1":
            if self.images:
                raise InferenceError("invalid_profile_target")
            allowed = {"operations_snapshot"}
        if self.target_kind not in allowed:
            raise InferenceError("invalid_profile_target")
        if self.target_kind == "listing_observation":
            if self.observation_id != self.target_id or self.revision != self.target_revision:
                raise InferenceError("observation_revision_mismatch")
        elif self.observation_id is not None:
            raise InferenceError("non_listing_observation_forbidden")
        if self.cohort_id is not None or self.cohort_generation is not None:
            raise InferenceError("unsupported_cohort")

    def signature(self, artifact: str) -> str:
        data = asdict(self) | {
            "artifact": artifact,
            "transformation": "512-v1",
            "options": {
                "num_ctx": CONTEXT_TOKENS,
                "num_predict": output_token_limit(self.prompt_version),
                "temperature": 0,
                "think": False,
                "visual_text": False,
            },
        }
        if self.prompt_version not in ASSISTANCE_PROFILES:
            for key in ("target_kind", "target_id", "target_revision", "context"):
                data.pop(key, None)
        else:
            data["assistance_profile"] = hashlib.sha256(
                (
                    assistance_prompt(self.prompt_version)
                    + json.dumps(assistance_schema(self.prompt_version, self.text), sort_keys=True)
                ).encode()
            ).hexdigest()
        if self.cohort_id is None:
            data.pop("cohort_id", None)
            data.pop("cohort_generation", None)
        if self.prompt_version == CONDITION_VERSION:
            data["condition_profile"] = hashlib.sha256(
                (CONDITION_PROMPT + json.dumps(CONDITION_SCHEMA, sort_keys=True)).encode()
            ).hexdigest()
        return hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()
