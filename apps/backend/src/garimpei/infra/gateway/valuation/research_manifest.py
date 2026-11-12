import json
from pathlib import Path
from typing import cast

from garimpei.domain.valuation.research_limits import InvalidResearchLimits, ResearchLimits


def load_research_limits(
    path: Path, root: Path, *, allow_controlled: bool = False
) -> ResearchLimits | None:
    try:
        raw = json.loads(path.read_text())
        if not isinstance(raw, dict):
            return None
        limits = ResearchLimits.parse(cast(dict[str, object], raw))
        if raw.get("automatic_activation") is False:
            return None
        evidence = [json.loads((root / p).read_text()) for p in limits.evidence_paths]
        kinds = {entry.get("source_kind") for entry in evidence if isinstance(entry, dict)}
        controlled_test = (
            allow_controlled and limits.environment == "eval-controlled" and kinds == {"controlled"}
        )
        if not controlled_test and not {"real", "controlled"}.issubset(kinds):
            return None
        if not all(isinstance(entry, dict) and entry.get("measurements") for entry in evidence):
            return None
        return limits
    except (OSError, ValueError, TypeError, InvalidResearchLimits):
        return None


def research_activation_reason(path: Path) -> str:
    try:
        raw = json.loads(path.read_text())
        if not isinstance(raw, dict) or raw.get("automatic_activation") is not False:
            return "research_limits_unmeasured"
        reason = raw.get("activation_block_reason")
        return (
            str(reason)
            if reason in {"real_geography_unproved", "final_union_validation_pending"}
            else "research_limits_unmeasured"
        )
    except (OSError, ValueError, TypeError):
        return "research_limits_unmeasured"
