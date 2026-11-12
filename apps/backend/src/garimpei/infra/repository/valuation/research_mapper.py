import hashlib
import json
from dataclasses import asdict

from garimpei.domain.listing.listing import Match
from garimpei.domain.listing.scope import Scope, Search
from garimpei.domain.valuation.product_catalog import product_title, product_values
from garimpei.domain.valuation.research import ResearchUnit
from garimpei.domain.valuation.research_limits import ResearchLimits
from garimpei.infra.persistence.research_models import ComparableInvestigation


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def research_term(product: str) -> str:
    return " ".join(product_title(dict(product_values(product))).split())


def unit(row: ComparableInvestigation, scope: Scope) -> ResearchUnit:
    query = Search(Match("product", row.product_key), row.term, "marketplace", purpose="research")
    from dataclasses import replace

    return ResearchUnit(
        row.id,
        row.generation,
        replace(scope, window=None),
        query,
        row.product_key,
        ResearchLimits.parse(row.limits),
        row.cursor,
        row.pages,
        tuple(str(item["external_id"]) for item in row.buffer),
    )


def policy_snapshot(limits: ResearchLimits) -> dict[str, object]:
    value = asdict(limits)
    value["evidence_paths"] = list(limits.evidence_paths)
    value["retry_delays_seconds"] = list(limits.retry_delays_seconds)
    return value
