from uuid import UUID

from garimpei.domain.valuation.research_diagnostic import (
    InterestCoverage,
    InvestigationView,
    ResearchDecisionView,
    ResearchDiagnostic,
)
from garimpei.domain.valuation.research_limits import ResearchLimits
from garimpei.infra.persistence.research_models import (
    ComparableInvestigation,
    ResearchCandidateDecision,
)


class PostgresComparableResearchQueries:
    def __init__(
        self,
        limits: ResearchLimits | None,
        corpus_date: str | None,
        corpus_hash: str | None,
        coverage: tuple[InterestCoverage, ...],
        version: str | None = None,
    ) -> None:
        self._version = version
        self._limits, self._date, self._hash, self._coverage = (
            limits,
            corpus_date,
            corpus_hash,
            coverage,
        )

    def read(self, listing: UUID | None = None) -> ResearchDiagnostic:
        rows = ComparableInvestigation.objects.order_by("-requested_at")
        if listing:
            rows = rows.filter(targets__listing_id=listing).distinct()
        investigations = []
        for row in rows[:20]:
            decisions = ResearchCandidateDecision.objects.select_related(
                "observation__listing"
            ).filter(query__investigation=row)
            if listing:
                decisions = decisions.filter(target__listing_id=listing)
            query = row.queries.order_by("-ordinal").first()
            observed = "Contexto geográfico ainda não confirmado."
            if query and query.observed.get("verified"):
                observed = (
                    "Localização e raio de "
                    + str(query.observed.get("radius_km"))
                    + " km confirmados na resposta da fonte."
                )
            investigations.append(
                InvestigationView(
                    row.id,
                    row.product_key,
                    row.term,
                    row.state,
                    row.reason,
                    row.pages,
                    row.details,
                    row.attempts,
                    row.next_attempt_at,
                    row.last_progress_at,
                    row.targets.filter(active=True).count(),
                    "CEP "
                    + str(row.context.get("cep", ""))
                    + " · raio "
                    + str(row.context.get("radius_km", ""))
                    + " km",
                    observed,
                    tuple(
                        ResearchDecisionView(
                            str(d.evidence.get("title", "")),
                            d.observation.listing.source,
                            d.observation.listing.canonical_url,
                            str(d.evidence["price"])
                            if d.evidence.get("price") is not None
                            else None,
                            d.observation.observed_at,
                            d.decision,
                            tuple(str(x) for x in d.reasons),
                        )
                        for d in decisions.order_by("recorded_at", "id")[:100]
                    ),
                    int(row.limits["max_pages_per_query"]),
                    int(row.limits["max_details_per_slice"]),
                    int(row.limits["max_slice_seconds"]),
                    int(row.limits["max_attempts_per_input"]),
                )
            )
        return ResearchDiagnostic(
            self._limits is not None,
            "research_ready" if self._limits else "research_limits_unmeasured",
            self._limits.policy_version if self._limits else None,
            self._date,
            self._hash,
            self._coverage,
            tuple(investigations),
            self._version,
        )
