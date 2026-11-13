"""Finite approved token budgets; profiles cannot request arbitrary generation caps."""

from garimpei.domain.assistance.review import ASSISTANCE_PROFILES
from garimpei.domain.inference.condition_evidence import VERSION as CONDITION_VERSION
from garimpei.domain.inference.errors import InferenceError

CONTEXT_TOKENS = 4096
TEXT_TOKENS = 2048
LEGACY_OUTPUT_TOKENS = 512
CONDITION_OUTPUT_TOKENS = 1024
# Preserve the visual headroom available before the F15-only output increase.
VISUAL_RESERVE_TOKENS = CONTEXT_TOKENS - TEXT_TOKENS - LEGACY_OUTPUT_TOKENS


def output_token_limit(profile: str) -> int:
    if profile == "local-evidence-v1" or profile in ASSISTANCE_PROFILES:
        return LEGACY_OUTPUT_TOKENS
    if profile == CONDITION_VERSION:
        return CONDITION_OUTPUT_TOKENS
    raise InferenceError("unsupported_prompt_or_schema", diagnostic="unsupported_profile")
