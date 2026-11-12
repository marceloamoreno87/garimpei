from dataclasses import dataclass
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
        FixedCep(),
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
        FixedCep(),
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
    assert "radius=500" in browser.calls[0] and "query=PlayStation+5" in browser.calls[0]
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
        source = FacebookMarketplace(browser, FixedCep(), CategoryCatalog("", "", ()))
        page = source.search(scope, scope.searches[0], None)
        assert page.window_proof == expected
        assert (page.continuation is None) == (expected is not None)

    # An empty intermediate page with a continuation is not proof of exhaustion.
    browser = RecordedNavigation((Feed((), True, True, "next-cursor"),), [])
    source = FacebookMarketplace(browser, FixedCep(), CategoryCatalog("", "", ()))
    page = source.search(scope, scope.searches[0], None)
    assert page.continuation is not None and page.window_proof is None

    browser = RecordedNavigation((Feed((), True, True, "next", True),), [])
    source = FacebookMarketplace(browser, FixedCep(), CategoryCatalog("", "", ()))
    page = source.search(scope, scope.searches[0], None)
    assert page.continuation is None and page.window_proof == "source_end_of_results"
