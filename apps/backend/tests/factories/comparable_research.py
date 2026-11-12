"""Named synthetic source: never imports or contacts a real browser/account."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from garimpei.domain.listing.listing import Candidate, Evidence
from garimpei.domain.listing.ports import Page, SearchContext, SourceFailure
from garimpei.domain.listing.scope import Scope, Search
from garimpei.domain.valuation.research_limits import ResearchLimits

NOW = datetime(2026, 11, 12, 12, tzinfo=UTC)
TITLE = "PlayStation 5 Slim Digital 825GB"
KEY = "sony:ps5:slim:digital:825gb"


def controlled_limits() -> ResearchLimits:
    """Test input, not a measurement manifest or authorization for automatic live research."""
    return ResearchLimits(
        "controlled-only-v1",
        NOW.isoformat(),
        "test",
        "0" * 64,
        ("controlled.json", "real-placeholder-not-a-measurement.json"),
        2,
        3,
        2,
        30,
        2,
        10,
        (5, 10, 20),
        40,
        3,
        4,
    )


def candidate(identity: str, price: str = "2300", title: str = TITLE) -> Candidate:
    evidence = Evidence(
        title=title,
        description="Usado. Funcionando perfeitamente.",
        condition="Usado — seminovo",
        published_at=NOW,
        published_at_source="controlled.source",
        price=Decimal(price),
        source_available=True,
    )
    return Candidate(identity, evidence, "detail")


@dataclass
class ControlledResearchSource:
    pages: list[tuple[Candidate, ...]] = field(
        default_factory=lambda: [tuple(candidate(str(18000 + i)) for i in range(5))]
    )
    failure: SourceFailure | None = None
    verified: bool = True
    calls: list[tuple[str, str | None]] = field(default_factory=list)

    def search(self, scope: Scope, query: Search, continuation: str | None) -> Page:
        self.calls.append(("search", continuation))
        if self.failure:
            raise self.failure
        index = int(continuation or "0")
        rows = self.pages[index] if self.pages else ()
        context = SearchContext(self.verified, -23.55, -46.63, 500, query.term)
        return Page(
            rows,
            str(index + 1) if index + 1 < len(self.pages) else None,
            window_proof="controlled_source_exhausted",
            source_context=context,
        )

    def detail(self, scope: Scope, external_id: str) -> Candidate:
        self.calls.append(("detail", external_id))
        if self.failure:
            raise self.failure
        return next(item for page in self.pages for item in page if item.external_id == external_id)


def scope() -> Scope:
    from garimpei.domain.listing.listing import Match

    return Scope(
        uuid4(),
        "facebook_marketplace",
        "01001000",
        1,
        "controlled-context",
        (Search(Match("category", "electronics"), "Eletrônicos", "marketplace"),),
    )


def seed_case(external_id: str, *, title: str = TITLE, price: str = "1000") -> "Listing":
    from dataclasses import asdict

    from garimpei.domain.listing.coverage import Coverage
    from garimpei.domain.listing.scope import Scope
    from garimpei.infra.persistence.listing_models import (
        CollectionCycle,
        CollectionState,
        Listing,
        ListingInterestMatch,
        ListingObservation,
    )
    from garimpei.infra.repository.listing.mapper import encode_evidence
    from garimpei.main import build_read_monitoring_configuration

    active = Scope.from_snapshot(build_read_monitoring_configuration().execute())
    assert active is not None
    state, _ = CollectionState.objects.get_or_create(
        configuration_id=active.configuration_id, source=active.source
    )
    cycle = CollectionCycle.objects.create(
        state=state,
        scope_key=active.key,
        revision=active.revision,
        started_at=NOW,
        finished_at=NOW,
        phase="complete",
    )
    listing, _ = Listing.objects.get_or_create(
        source=active.source,
        external_id=external_id,
        defaults=dict(
            canonical_url=f"https://www.facebook.com/marketplace/item/{external_id}/",
            first_seen_at=NOW,
            origin="initial_load",
        ),
    )
    evidence = candidate(external_id, price, title).evidence
    observation = ListingObservation.objects.create(
        listing=listing,
        cycle=cycle,
        ordinal=listing.ordinal + 1,
        observed_at=NOW,
        price=evidence.price,
        freight=None,
        evidence=encode_evidence(evidence),
        coverage=asdict(Coverage("confirmed", "unknown", None, "controlled", "controlled")),
        provenance={"title": "detail", "price": "detail"},
    )
    for search in active.searches:
        ListingInterestMatch.objects.create(
            observation=observation, kind=search.interest.kind, key=search.interest.key
        )
    listing.latest, listing.ordinal, listing.known_price = (
        observation,
        observation.ordinal,
        observation,
    )
    listing.save()
    return listing


from garimpei.infra.persistence.listing_models import Listing  # noqa: E402
from tests.factories.valuation import ValuationSource  # noqa: E402
from tests.factories.valuation import listing as fixture_listing  # noqa: E402


@dataclass
class ResearchLoopbackSource(ValuationSource):
    research_failure: bool = False
    rows: dict[str, dict[str, object]] = field(
        default_factory=lambda: {"18801": fixture_listing("18801", "1000,00")}
    )
    timings: list[dict[str, object]] = field(default_factory=list)

    def respond(self, path: str, parameters: dict[str, str]) -> tuple[int, dict[str, object]]:
        import time

        start = time.perf_counter()
        if path == "/search" and parameters.get("kind") == "product":
            result = (503, {}) if self.research_failure else self._research_page(parameters)
        elif path.startswith("/detail/1881"):
            identity = path.removeprefix("/detail/")
            result = (
                200,
                fixture_listing(identity, "2300,00") | {"context_cep": parameters["cep"]},
            )
        else:
            result = super().respond(path, parameters)
        self.timings.append(
            dict(
                operation="detail"
                if path.startswith("/detail/")
                else "query"
                if path == "/search"
                else "other",
                seconds=time.perf_counter() - start,
            )
        )
        return result

    @staticmethod
    def _research_page(parameters: dict[str, str]) -> tuple[int, dict[str, object]]:
        return 200, dict(
            context={k: v for k, v in parameters.items() if k != "page"},
            cards=[fixture_listing(str(18810 + i), "2300,00") for i in range(5)],
            next=None,
            end=True,
            empty=False,
            observed_geography=dict(
                cep=parameters["cep"],
                latitude=-23.55,
                longitude=-46.63,
                city="São Paulo",
                state="SP",
                accuracy_m=None,
                radius_km=500,
                query=parameters["term"],
            ),
        )


class ForbiddenResearchStore:
    """The timing boundary must not perform repository or source work."""

    def claim(self) -> "ResearchUnit | None":
        raise AssertionError("Unexpected repository claim")

    def page(self, unit: "ResearchUnit", page: Page) -> "ResearchUnit | None":
        raise AssertionError("Unexpected page publication")

    def detail(self, unit: "ResearchUnit", candidate: Candidate) -> "ResearchUnit | None":
        raise AssertionError("Unexpected detail publication")

    def failed(self, unit: "ResearchUnit", failure: SourceFailure) -> None:
        raise AssertionError("Unexpected failure publication")

    def yield_slice(self, unit: "ResearchUnit") -> None:
        raise AssertionError("Unexpected scheduling")


from garimpei.domain.valuation.research import ResearchUnit  # noqa: E402
