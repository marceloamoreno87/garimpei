"""Reviewed recovery allowlist for product provenance and bounded comparable research."""

from django.db.models import Model

from garimpei.infra.persistence.identity_models import (
    IdentityProgress,
    ManualIdentityRevision,
    ProductIdentification,
)
from garimpei.infra.persistence.research_models import (
    ComparableInvestigation,
    InvestigationTarget,
    ResearchCandidateDecision,
    ResearchQuery,
)

RESEARCH_SCHEMA: dict[str, tuple[type[Model], tuple[str, ...]]] = {
    "runtime.manualidentityrevision": (
        ManualIdentityRevision,
        (
            "listing",
            "revision",
            "observation",
            "action",
            "resolution",
            "values",
            "reviewed_conflicts",
            "recorded_at",
            "previous",
        ),
    ),
    "runtime.productidentification": (
        ProductIdentification,
        (
            "listing",
            "observation",
            "manual_revision",
            "policy",
            "state",
            "product_key",
            "result",
            "recorded_at",
        ),
    ),
    "runtime.identityprogress": (
        IdentityProgress,
        (
            "manual_revision",
            "manual",
            "current",
        ),
    ),
    "runtime.comparableinvestigation": (
        ComparableInvestigation,
        (
            "signature",
            "product_key",
            "configuration_id",
            "configuration_revision",
            "origin_interest",
            "scope_key",
            "context",
            "limits",
            "term",
            "policy",
            "state",
            "reason",
            "pages",
            "details",
            "attempts",
            "failures",
            "last_turn",
            "generation",
            "next_attempt_at",
            "lease_until",
            "last_progress_at",
            "requested_at",
            "cursor",
            "signatures",
            "buffer",
            "cycle",
        ),
    ),
    "runtime.investigationtarget": (
        InvestigationTarget,
        (
            "investigation",
            "listing",
            "observation",
            "manual_revision",
            "configuration_revision",
            "active",
        ),
    ),
    "runtime.researchquery": (
        ResearchQuery,
        (
            "investigation",
            "ordinal",
            "term",
            "requested",
            "observed",
            "state",
            "reason",
            "requested_at",
            "confirmed_at",
        ),
    ),
    "runtime.researchcandidatedecision": (
        ResearchCandidateDecision,
        (
            "query",
            "target",
            "observation",
            "policy",
            "decision",
            "reasons",
            "evidence",
            "recorded_at",
        ),
    ),
}
