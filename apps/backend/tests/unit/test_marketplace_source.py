from dataclasses import dataclass
from typing import Literal
from uuid import uuid4

import pytest

from garimpei.domain.listing.geography import Point
from garimpei.domain.listing.ports import ListingUnavailable, SourceFailure
from garimpei.domain.listing.scope import Scope
from garimpei.domain.monitoring.snapshot import MonitoringSnapshot
from garimpei.domain.monitoring.values import Category, CategoryCatalog
from garimpei.infra.gateway.listing.facebook_marketplace import FacebookMarketplace
from garimpei.infra.gateway.listing.marketplace_browser import SearchFilters
from garimpei.infra.gateway.listing.relay_parser import Feed, JsonObject


class NativeCategoryNavigation:
    def search(
        self, url: str, filters: SearchFilters
    ) -> tuple[tuple[JsonObject, ...], Feed | None]:
        from urllib.parse import urlsplit

        if urlsplit(url).path != "/marketplace/category/cameras/":
            return ({"initialRouteInfo": {"route": {"params": {"section": "browse"}}}},), None
        return (
            {"initialRouteInfo": {"route": {"params": {"category_id": "cameras"}}}},
            {
                "variables": {
                    "params": {
                        "browse_request_params": {
                            "filter_location_latitude": filters.origin.latitude,
                            "filter_location_longitude": filters.origin.longitude,
                            "filter_radius_km": filters.radius_km,
                            "commerce_search_sort_by": "CREATION_TIME_DESCEND",
                        }
                    }
                }
            },
        ), Feed((), False, True)

    def navigate(self, url: str) -> tuple[tuple[JsonObject, ...], Feed | None]:
        raise AssertionError("No detail expected for verified empty category")

    def scroll(self) -> Feed:
        raise AssertionError("No continuation expected for verified empty category")

    def close(self) -> None:
        pass


def test_category_navigation_uses_the_verified_native_category_route() -> None:
    scope = Scope.from_snapshot(
        MonitoringSnapshot(
            configured=True,
            configuration_id=uuid4(),
            revision=1,
            cep="01001000",
            category_ids=("cameras",),
        )
    )
    assert scope is not None
    source = FacebookMarketplace(
        NativeCategoryNavigation(),
        FixedCep().resolve("01001000"),
        CategoryCatalog(
            "",
            "",
            (
                Category(
                    "cameras",
                    "Câmeras",
                    None,
                    "https://www.facebook.com/marketplace/category/cameras/",
                ),
            ),
        ),
    )
    page = source.search(scope, scope.searches[0], None)
    assert page.candidates == () and page.continuation is None and page.diagnostic is None


@dataclass
class RecordedNavigation:
    pages: tuple[Feed, ...]
    calls: list[str]
    index: int = 0
    detail_rows: tuple[JsonObject, ...] = ()

    def navigate(self, url: str) -> tuple[tuple[JsonObject, ...], Feed | None]:
        self.calls.append(url)
        if "/marketplace/item/" in url:
            return self.detail_rows, None
        self.index = 0
        return (
            {"initialRouteInfo": {"route": {"params": {"query": "PlayStation 5", "radius": 20}}}},
        ), self.pages[0]

    def search(
        self, url: str, filters: SearchFilters
    ) -> tuple[tuple[JsonObject, ...], Feed | None]:
        rows, page = self.navigate(url)
        proof: JsonObject = {
            "variables": {
                "params": {
                    "browse_request_params": {
                        "filter_location_latitude": filters.origin.latitude,
                        "filter_location_longitude": filters.origin.longitude,
                        "filter_radius_km": filters.radius_km,
                        "commerce_search_sort_by": "CREATION_TIME_DESCEND",
                    }
                }
            }
        }
        return (proof,) + rows, page

    def scroll(self) -> Feed:
        self.index += 1
        return self.pages[self.index]

    def close(self) -> None:
        pass


class FixedCep:
    def resolve(self, cep: str) -> Point:
        assert cep == "01001000"
        return Point(-23.55, -46.63, None, "São Paulo", "SP")


def test_live_source_search_continuation_and_detail_evidence() -> None:
    row: JsonObject = {
        "id": "101",
        "marketplace_listing_title": "PlayStation 5",
        "listing_price": {"amount": "2300.00", "currency": "BRL"},
    }
    browser = RecordedNavigation(
        (Feed((row,), True, False), Feed((row | {"id": "102"},), False, False)),
        [],
    )
    source = FacebookMarketplace(
        browser,
        FixedCep().resolve("01001000"),
        CategoryCatalog(
            "",
            "",
            (
                Category(
                    "479353692612078",
                    "Electronics",
                    None,
                    "https://www.facebook.com/marketplace/category/search/",
                ),
            ),
        ),
    )
    scope = Scope.from_snapshot(
        MonitoringSnapshot(
            configured=True,
            configuration_id=uuid4(),
            revision=1,
            cep="01001000",
            product_names=("PlayStation 5",),
        )
    )
    assert scope is not None
    query = scope.searches[0]
    first = source.search(scope, query, None)
    second = source.search(scope, query, first.continuation)
    assert first.candidates[0].external_id == "101"
    assert second.candidates[0].external_id == "102" and second.continuation is None
    assert first.diagnostic is None and first.candidates[0].evidence.pickup_scope_verified is None
    assert "radius=20" in browser.calls[0] and "query=PlayStation+5" in browser.calls[0]
    browser.detail_rows = ({"_garimpei_unavailable_product_id": "101"}, row)
    with pytest.raises(ListingUnavailable) as unavailable:
        source.detail(scope, "101")
    assert unavailable.value.external_id == "101"
    assert unavailable.value.evidence == "source_unavailable_product"
    with pytest.raises(SourceFailure, match="listing_detail_unavailable"):
        source.detail(scope, "102")


def test_source_boundary_requires_native_order_and_observed_monotonicity() -> None:
    from dataclasses import replace
    from datetime import UTC, datetime, timedelta

    from garimpei.domain.listing.window import PublicationWindow

    end = datetime(2026, 11, 11, 12, tzinfo=UTC)
    window = PublicationWindow.ending_at(end)
    scope = Scope.from_snapshot(
        MonitoringSnapshot(
            configured=True,
            configuration_id=uuid4(),
            revision=1,
            cep="01001000",
            product_names=("PlayStation 5",),
        )
    )
    assert scope is not None
    scope = replace(scope, window=window)

    def row(identity: str, stamp: datetime | None) -> JsonObject:
        return {
            "id": identity,
            "marketplace_listing_title": "PlayStation 5",
            "creation_time": stamp.timestamp() if stamp else None,
        }

    for stamps, expected in (
        ((end, window.start - timedelta(seconds=1)), None),
        (
            (window.start - timedelta(seconds=1), window.start - timedelta(seconds=2)),
            "chronological_boundary",
        ),
        ((window.start - timedelta(seconds=1), end), None),
        ((None, window.start - timedelta(seconds=1)), None),
    ):
        browser = RecordedNavigation(
            (Feed(tuple(row(str(101 + i), stamp) for i, stamp in enumerate(stamps)), True, False),),
            [],
        )
        source = FacebookMarketplace(
            browser, FixedCep().resolve("01001000"), CategoryCatalog("", "", ())
        )
        page = source.search(scope, scope.searches[0], None)
        assert page.window_proof == expected
        assert (page.continuation is None) == (expected is not None)

    # An empty intermediate page with a continuation is not proof of exhaustion.
    browser = RecordedNavigation((Feed((), True, True, "next-cursor"),), [])
    source = FacebookMarketplace(
        browser, FixedCep().resolve("01001000"), CategoryCatalog("", "", ())
    )
    page = source.search(scope, scope.searches[0], None)
    assert page.continuation is not None and page.window_proof is None

    browser = RecordedNavigation((Feed((), True, True, "next", True),), [])
    source = FacebookMarketplace(
        browser, FixedCep().resolve("01001000"), CategoryCatalog("", "", ())
    )
    page = source.search(scope, scope.searches[0], None)
    assert page.continuation is None and page.window_proof == "source_end_of_results"


def test_media_carousel_fragment_binds_only_to_verified_listing_identity() -> None:
    row: JsonObject = {
        "id": "101",
        "marketplace_listing_title": "PlayStation 5",
        "listing_price": {"amount": "2300.00", "currency": "BRL"},
    }
    browser = RecordedNavigation((), [])
    browser.detail_rows = (
        row,
        {
            "id": "101",
            "listing_photos": [
                {
                    "id": "photo-a",
                    "image": {"uri": "https://a.fbcdn.net/a", "width": 720, "height": 960},
                }
            ],
        },
        {
            "id": "other-listing",
            "listing_photos": [
                {
                    "id": "photo-b",
                    "image": {"uri": "https://a.fbcdn.net/b", "width": 1200, "height": 1200},
                }
            ],
        },
    )
    source = FacebookMarketplace(
        browser, FixedCep().resolve("01001000"), CategoryCatalog("", "", ())
    )
    scope = Scope.from_snapshot(
        MonitoringSnapshot(
            configured=True,
            configuration_id=uuid4(),
            revision=1,
            cep="01001000",
            product_names=("PlayStation 5",),
        )
    )
    assert scope is not None
    candidate = source.detail(scope, "101")
    assert candidate.evidence.media is not None
    assert candidate.evidence.media.complete
    assert [photo.key for photo in candidate.evidence.media.photos] == ["photo-a"]
    assert candidate.evidence.media.photos[0].variants[0].width == 720


def test_comparable_research_does_not_inherit_publication_age_filter() -> None:
    from dataclasses import replace
    from urllib.parse import parse_qs, urlsplit

    from garimpei.domain.listing.listing import Match
    from garimpei.domain.listing.scope import Search
    from garimpei.infra.gateway.listing.marketplace_browser import MarketplaceBrowser

    scope = Scope.from_snapshot(
        MonitoringSnapshot(
            configured=True,
            configuration_id=uuid4(),
            revision=1,
            cep="01001000",
            product_names=("PlayStation 5",),
        )
    )
    assert scope is not None
    source = FacebookMarketplace(
        RecordedNavigation((Feed((), False, True),), []),
        FixedCep().resolve("01001000"),
        CategoryCatalog("", "", ()),
    )
    query = Search(
        Match("product", "sony:ps5:slim:disc:1tb"),
        "PlayStation 5 slim disco 1tb",
        "marketplace",
        purpose="research",
    )
    assert "daysSinceListed" not in parse_qs(urlsplit(source._url(scope, query)).query)
    assert parse_qs(urlsplit(source._url(scope, replace(query, purpose="active"))).query)[
        "daysSinceListed"
    ] == ["3"]
    browser = MarketplaceBrowser.__new__(MarketplaceBrowser)
    browser._filters = SearchFilters(
        Point(-23.55, -46.63, None, "São Paulo", "SP"), 500, None, all_publication_dates=True
    )
    observed: JsonObject = {"commerce_search_and_rp_ctime_days": "20000;19999"}
    browser._patch_filters(observed)
    assert "commerce_search_and_rp_ctime_days" not in observed
    assert observed["filter_radius_km"] == 500


@pytest.mark.parametrize("purpose", ["active", "research"])
def test_marketplace_search_requests_twenty_km_around_injected_source_origin(
    purpose: Literal["active", "research"],
) -> None:
    from urllib.parse import parse_qs, urlsplit

    from garimpei.domain.listing.listing import Match
    from garimpei.domain.listing.scope import Search

    class CaptureNavigation(RecordedNavigation):
        requested_filters: SearchFilters | None = None

        def search(
            self, url: str, filters: SearchFilters
        ) -> tuple[tuple[JsonObject, ...], Feed | None]:
            self.requested_filters = filters
            return super().search(url, filters)

    browser = CaptureNavigation((Feed((), False, True),), [])
    source = FacebookMarketplace(
        browser, FixedCep().resolve("01001000"), CategoryCatalog("", "", ())
    )
    scope = Scope(uuid4(), "facebook_marketplace", "01001000", 1, "scope", ())
    query = Search(
        Match("product", "playstation 5"), "PlayStation 5", "marketplace", purpose=purpose
    )
    source.search(scope, query, None)
    assert browser.requested_filters is not None
    assert browser.requested_filters.radius_km == 20
    assert browser.requested_filters.origin == FixedCep().resolve("01001000")
    assert parse_qs(urlsplit(browser.calls[0]).query)["radius"] == ["20"]


def test_research_does_not_validate_a_saved_five_hundred_km_context() -> None:
    from garimpei.domain.listing.listing import Match
    from garimpei.domain.listing.scope import Search

    class SavedRadiusNavigation(RecordedNavigation):
        def search(
            self, url: str, filters: SearchFilters
        ) -> tuple[tuple[JsonObject, ...], Feed | None]:
            rows, feed = super().search(url, filters)
            metadata: JsonObject = {
                "variables": {
                    "params": {
                        "browse_request_params": {
                            "filter_location_latitude": filters.origin.latitude,
                            "filter_location_longitude": filters.origin.longitude,
                            "filter_radius_km": 500,
                        }
                    }
                }
            }
            return (metadata,) + rows[1:], feed

    browser = SavedRadiusNavigation((Feed((), False, True),), [])
    source = FacebookMarketplace(
        browser, FixedCep().resolve("01001000"), CategoryCatalog("", "", ())
    )
    scope = Scope(uuid4(), "facebook_marketplace", "01001000", 1, "scope", ())
    page = source.search(
        scope,
        Search(
            Match("product", "playstation 5"), "PlayStation 5", "marketplace", purpose="research"
        ),
        None,
    )
    assert page.source_context is not None
    assert page.source_context.radius_km == 500
    assert not page.source_context.verified
    assert page.diagnostic == "search_geography_unverified"


def test_initial_page_matching_radius_does_not_prove_graphql_results() -> None:
    from garimpei.domain.listing.listing import Match
    from garimpei.domain.listing.scope import Search

    class InitialOnlyNavigation(RecordedNavigation):
        def search(
            self, url: str, filters: SearchFilters
        ) -> tuple[tuple[JsonObject, ...], Feed | None]:
            rows, feed = super().search(url, filters)
            return rows + ({"_garimpei_response_context_unverified": True},), feed

    browser = InitialOnlyNavigation((Feed((), False, True),), [])
    source = FacebookMarketplace(
        browser, FixedCep().resolve("01001000"), CategoryCatalog("", "", ())
    )
    scope = Scope(uuid4(), "facebook_marketplace", "01001000", 1, "scope", ())
    page = source.search(
        scope,
        Search(
            Match("product", "playstation 5"), "PlayStation 5", "marketplace", purpose="research"
        ),
        None,
    )
    assert page.source_context is not None
    assert page.source_context.radius_km == 20
    assert not page.source_context.verified
    assert page.diagnostic == "search_geography_unverified"
