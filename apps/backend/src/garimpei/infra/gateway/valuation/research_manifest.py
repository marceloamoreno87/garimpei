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
