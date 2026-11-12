from pathlib import Path
from uuid import uuid4

import pytest

from garimpei.domain.listing.geography import Point
from garimpei.domain.listing.listing import Match
from garimpei.domain.listing.ports import SourceFailure
from garimpei.domain.listing.scope import Scope, Search
from garimpei.domain.monitoring.values import CategoryCatalog
from garimpei.infra.gateway.listing.facebook_marketplace import FacebookMarketplace
from garimpei.infra.gateway.listing.marketplace_browser import MarketplaceBrowser, SearchFilters
from garimpei.infra.gateway.listing.relay_parser import Feed, JsonObject


class Geocoding:
    def resolve(self, _cep: str) -> Point:
        return Point(-23.55, -46.63, None, "São Paulo", "SP")


class ContinuationBrowser:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def search(
        self, url: str, filters: SearchFilters
    ) -> tuple[tuple[JsonObject, ...], Feed | None]:
        self.calls.append("context")
        return (
            {"initialRouteInfo": {"route": {"params": {"query": "PS5 Slim"}}}},
            {
                "variables": {
                    "params": {
                        "browse_request_params": {
                            "filter_location_latitude": filters.origin.latitude,
                            "filter_location_longitude": filters.origin.longitude,
                            "filter_radius_km": filters.radius_km,
                        }
                    }
                }
            },
        ), Feed((), True, True, "opaque-first")

    def continue_from(self, cursor: str) -> Feed:
        self.calls.append(cursor)
        return Feed((), False, True, None)

    def scroll(self) -> Feed:
        raise AssertionError("Session-local counter is not durable continuation")

    def navigate(self, url: str) -> tuple[tuple[JsonObject, ...], Feed | None]:
        return (), None

    def close(self) -> None:
        pass


def test_safe_cursor_can_reconstruct_in_a_new_adapter() -> None:
    browser = ContinuationBrowser()
    source = FacebookMarketplace(browser, Geocoding(), CategoryCatalog("", "", ()))
    scope = Scope(uuid4(), "facebook_marketplace", "01001000", 4, "scope", ())
    query = Search(Match("product", "ps5 slim"), "PS5 Slim", "marketplace")
    page = source.search(scope, query, "source:opaque-previous")
    assert browser.calls == ["context", "opaque-previous"]
    assert page.rebuilt and page.traversed_pages == 2
    assert page.continuation is None


class LongCursorBrowser(ContinuationBrowser):
    def __init__(self, cursor: str) -> None:
        super().__init__()
        self.cursor = cursor

    def search(
        self, url: str, filters: SearchFilters
    ) -> tuple[tuple[JsonObject, ...], Feed | None]:
        rows, _ = super().search(url, filters)
        return rows, Feed((), True, True, self.cursor)


def test_native_cursor_survives_new_adapter_without_assuming_base64_or_480_bytes() -> None:
    # The real source produced 1,674 characters outside the assumed base64 alphabet.
    # Use synthetic opaque data, never a captured authenticated cursor.
    cursor = '{"offset":"' + "x" * 1650 + '","page":2}'
    first_browser = LongCursorBrowser(cursor)
    first_source = FacebookMarketplace(first_browser, Geocoding(), CategoryCatalog("", "", ()))
    scope = Scope(uuid4(), "facebook_marketplace", "01001000", 4, "scope", ())
    query = Search(Match("product", "ps5 slim"), "PS5 Slim", "marketplace")
    first_page = first_source.search(scope, query, None)
    assert first_page.continuation == "source:" + cursor

    resumed_browser = LongCursorBrowser(cursor)
    resumed_source = FacebookMarketplace(resumed_browser, Geocoding(), CategoryCatalog("", "", ()))
    second_page = resumed_source.search(scope, query, first_page.continuation)
    assert resumed_browser.calls == ["context", cursor]
    assert second_page.rebuilt and second_page.traversed_pages == 2
    assert second_page.continuation is None


@pytest.mark.parametrize("cursor", ["x" * 4097, "opaque\nvalue", "opaque\x00value", "é"])
def test_native_cursor_rejects_controls_oversize_and_non_ascii(cursor: str) -> None:
    browser = ContinuationBrowser()
    source = FacebookMarketplace(browser, Geocoding(), CategoryCatalog("", "", ()))
    scope = Scope(uuid4(), "facebook_marketplace", "01001000", 4, "scope", ())
    query = Search(Match("product", "ps5 slim"), "PS5 Slim", "marketplace")
    with pytest.raises(SourceFailure, match="cursor_expired"):
        source.search(scope, query, "source:" + cursor)
    assert browser.calls == []


class RecordingRequestBrowser(MarketplaceBrowser):
    def __init__(self, state_path: Path) -> None:
        super().__init__(state_path, 20, 0)
        self._query_payload = {"variables": {}}
        self.received: str | None = None

    def _request_page(self) -> Feed:
        self.received = self._cursor
        return Feed((), False, True)


def test_browser_continuation_preserves_the_exact_4096_character_json_value(tmp_path: Path) -> None:
    cursor = ' {"opaque":"' + "x" * 4081 + '"} '
    assert len(cursor) == 4096
    browser = RecordingRequestBrowser(tmp_path / "synthetic-state.json")
    try:
        assert not browser.continue_from(cursor).has_next
        assert browser.received == cursor
    finally:
        browser.close()
