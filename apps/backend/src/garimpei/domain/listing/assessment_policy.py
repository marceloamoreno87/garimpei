import re

from garimpei.domain.listing.assessment import AssessmentDecision, Finding
from garimpei.domain.listing.condition import automatic_condition
from garimpei.domain.listing.listing import Evidence
from garimpei.domain.listing.text_normalization import normalize_text

POLICY_VERSION = "condition-policy-v1"
CATEGORIES = frozenset({"electronics", "camera", "computer", "console", "headphone", "television"})


def decide(
    evidence: Evidence,
    category: str,
    findings: tuple[Finding, ...],
    *,
    complete: bool,
    reason: str = "insufficient_visual_evidence",
    conflicts: bool = False,
) -> AssessmentDecision:
    text = automatic_condition(evidence)
    visual = any(_main_visual(f) for f in findings)
    clear = any(_main_visual(f) and f.assessment == "clear_defect" for f in findings)
    suspect = any(f.assessment in {"suspected", "unknown"} for f in findings)
    identity = any(f.dimension == "identity" and f.assessment != "declaration" for f in findings)
    supported = category in CATEGORIES
    sufficient = complete and visual and supported and not (suspect or conflicts or identity)
    if text.condition == "defect" or clear:
        return AssessmentDecision("defect", sufficient, "clear_defect")
    if identity:
        return AssessmentDecision("uncertain", False, "identity_conflict")
    if conflicts or suspect:
        return AssessmentDecision(
            "uncertain",
            False,
            "unresolved_conflict" if conflicts else "insufficient_visual_evidence",
        )
    if text.reasons:
        return AssessmentDecision("uncertain", False, text.reasons[0])
    if not supported:
        return AssessmentDecision("uncertain", False, "unsupported_category")
    if text.condition != "good":
        return AssessmentDecision("uncertain", False, "function_not_declared")
    if not complete or not visual:
        return AssessmentDecision("uncertain", False, reason)
    return AssessmentDecision("good", True, "seller_declared_visual_assessment")


def _main_visual(finding: Finding) -> bool:
    accessory = re.match(
        r"^(?:o |a |um |uma )?(?:controle|cabo|carregador|acessorio)\b",
        normalize_text(finding.description),
    )
    return (
        finding.dimension == "appearance"
        and not accessory
        and any(r.kind == "image" for r in finding.references)
    )
