from uuid import uuid4

from garimpei.domain.listing.geography import Point
from garimpei.domain.listing.listing import Match
from garimpei.domain.listing.scope import Scope, Search
from garimpei.domain.monitoring.values import CategoryCatalog
from garimpei.infra.gateway.listing.facebook_marketplace import FacebookMarketplace
from garimpei.infra.gateway.listing.marketplace_browser import SearchFilters
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
        return ({"initialRouteInfo": {"route": {"params": {"query": "PS5 Slim"}}}},), Feed(
            (), True, True, "opaque-first"
        )

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
