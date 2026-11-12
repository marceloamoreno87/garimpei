import logging
from dataclasses import replace
from datetime import datetime
from typing import TYPE_CHECKING

from garimpei.domain.listing.geography import Point
from garimpei.domain.listing.listing import Candidate
from garimpei.domain.listing.ports import ListingUnavailable, Page, SearchContext, SourceFailure
from garimpei.infra.gateway.listing.marketplace_browser import (
    MarketplaceContinuation,
    MarketplaceNavigation,
    SearchFilters,
    valid_source_cursor,
)

if TYPE_CHECKING:
    from garimpei.domain.listing.ports import Geocoding
    from garimpei.domain.monitoring.values import CategoryCatalog
    from garimpei.infra.gateway.listing.relay_parser import Feed, JsonObject
from garimpei.domain.listing.scope import Scope, Search

logger = logging.getLogger(__name__)


class UnavailableMarketplace:
    """Live access awaits the authorized source profile and verification of coverage."""

    def search(self, _scope: Scope, _query: Search, _continuation: str | None) -> Page:
        raise SourceFailure("source_profile_unavailable", access=True)

    def detail(self, _scope: Scope, _external_id: str) -> Candidate:
        raise SourceFailure("source_profile_unavailable", access=True)

    def resolve(self, _cep: str) -> Point | None:
        return None


class FacebookMarketplace:
    def __init__(
        self,
        browser: MarketplaceNavigation,
        geocoding: "Geocoding",
        catalog: "CategoryCatalog",
    ) -> None:
        self._browser = browser
        self._geocoding = geocoding
        self._catalog = catalog
        self._query_key: str | None = None
        self._page_number = 0
        self._context_reason: str | None = None
        self._origin: Point | None = None
        self._source_context: SearchContext | None = None
        self._native_sort = False
        self._ordered = True
        self._last_date: datetime | None = None

    def search(self, scope: Scope, query: Search, continuation: str | None) -> Page:
        if continuation is not None and continuation.startswith("source:"):
            return self._resume(scope, query, continuation.removeprefix("source:"))
        if continuation is None:
            url = self._url(scope, query)
            assert self._origin is not None
            rows, feed = self._browser.search(
                url,
                SearchFilters(
                    self._origin,
                    20 if query.modality == "pickup" else 500,
                    scope.window,
                    all_publication_dates=query.purpose == "research",
                ),
            )
            self._query_key = f"{scope.key}:{scope.revision}:{query.key}:{query.term}"
            self._ordered = True
            self._last_date = None
            self._page_number = 1
            self._context_reason = self._context(rows, query)
        elif (
            self._query_key == f"{scope.key}:{scope.revision}:{query.key}:{query.term}"
            and continuation == str(self._page_number + 1)
        ):
            feed = self._browser.scroll()
            self._page_number += 1
        else:
            raise SourceFailure("continuation_scope_mismatch")
        if feed is None:
            raise SourceFailure("search_feed_unavailable")
        return self._page(feed, query, scope)

    def _resume(self, scope: Scope, query: Search, cursor: str) -> Page:
        if not valid_source_cursor(cursor) or not isinstance(
            self._browser, MarketplaceContinuation
        ):
            raise SourceFailure("cursor_expired")
        context_key = f"{scope.key}:{scope.revision}:{query.key}:{query.term}"
        rebuilt = self._query_key != context_key
        if rebuilt:
            self.search(scope, query, None)
        if self._context_reason:
            raise SourceFailure(self._context_reason)
        try:
            feed = self._browser.continue_from(cursor)
        except SourceFailure as failure:
            if failure.access or failure.retry_after:
                raise
            raise SourceFailure("cursor_expired") from None
        self._page_number += 1
        return replace(
            self._page(feed, query, scope), rebuilt=rebuilt, traversed_pages=2 if rebuilt else 1
        )

    def _page(self, feed: "Feed", query: Search, scope: Scope) -> Page:
        from garimpei.infra.gateway.listing.relay_parser import listing_from

        candidates = tuple(
            candidate
            for row in feed.listings
            if (candidate := listing_from(row, detail=False, match=query.interest)) is not None
        )
        candidates = tuple(
            replace(
                candidate,
                evidence=replace(
                    candidate.evidence,
                    pickup_scope_verified=(
                        True
                        if query.modality == "pickup" and self._context_reason is None
                        else None
                    ),
                ),
            )
            for candidate in candidates
        )
        if not candidates and not feed.empty:
            raise SourceFailure("unverified_empty")
        if feed.has_next is None:
            raise SourceFailure("unverified_boundary")
        boundary = self._boundary(candidates, scope)
        exhausted = not feed.has_next or feed.main_results_ended
        page = Page(
            candidates,
            None
            if boundary or exhausted
            else "source:" + feed.cursor
            if feed.cursor and valid_source_cursor(feed.cursor)
            else str(self._page_number + 1),
            len(feed.listings) - len(candidates),
            self._context_reason,
            "chronological_boundary"
            if boundary
            else "source_end_of_results"
            if feed.main_results_ended and exhausted
            else "source_exhausted"
            if exhausted
            else None,
        )

        page = replace(page, source_context=self._source_context)
        if (
            query.purpose == "research"
            and page.continuation is not None
            and not page.continuation.startswith("source:")
        ):
            page = replace(
                page, continuation=None, diagnostic=page.diagnostic or "native_cursor_unavailable"
            )
        self._log_page(query, feed, page)
        return page

    def _log_page(self, query: Search, feed: "Feed", page: Page) -> None:
        stamps = [
            item.evidence.published_at.isoformat()
            for item in page.candidates
            if item.evidence.published_at is not None
        ]
        logger.info(
            "collection_source_page",
            extra={
                "event": "collection_source_page",
                "source_query": query.key,
                "source_page": self._page_number,
                "source_count": len(page.candidates),
                "source_first_publication": stamps[0] if stamps else None,
                "source_last_publication": stamps[-1] if stamps else None,
                "source_has_next": feed.has_next,
                "source_main_results_ended": feed.main_results_ended,
                "source_window_proof": page.window_proof,
                "source_ordered": self._ordered,
                "source_native_sort": self._native_sort,
                "source_geography_verified": query.modality == "pickup"
                and self._context_reason is None,
                "source_radius_km": 20 if query.modality == "pickup" else 500,
            },
        )

    def _boundary(self, candidates: tuple[Candidate, ...], scope: Scope) -> bool:
        for candidate in candidates:
            stamp = candidate.evidence.published_at
            if stamp is None:
                self._ordered = False
                continue
            if self._last_date is not None and stamp > self._last_date:
                self._ordered = False
            self._last_date = stamp
        return (
            scope.window is not None
            and self._native_sort
            and self._ordered
            and bool(candidates)
            and all(
                (stamp := item.evidence.published_at) is not None and stamp < scope.window.start
                for item in candidates
            )
        )

    def _url(self, scope: Scope, query: Search) -> str:
        from urllib.parse import urlencode

        point = self._geocoding.resolve(scope.cep)
        if point is None:
            raise SourceFailure("geocoding_coordinates_unavailable")
        self._origin = point
        params: dict[str, str] = {
            "sortBy": "creation_time_descend",
            "daysSinceListed": str(max(3, (scope.window.end - scope.window.start).days + 1))
            if scope.window
            else "3",
            "radius": "20" if query.modality == "pickup" else "500",
            "latitude": str(point.latitude),
            "longitude": str(point.longitude),
            "exact": "true",
        }
        if query.purpose == "research":
            params.pop("daysSinceListed", None)
        route = "search/"
        if query.interest.kind == "product":
            params["query"] = query.term + (" envio" if query.modality == "shipping" else "")
        else:
            route, category_params = self._category(query.interest.key)
            params.update(category_params)
            if query.modality == "shipping" and "query" in params:
                params["query"] += " envio"
        # Native category routes are rooted at /marketplace/category/, without a city prefix.
        base = "https://www.facebook.com/marketplace/" + (
            "" if route.startswith("category/") else "saopaulo/"
        )
        return base + route + "?" + urlencode(params)

    def _category(self, identity: str) -> tuple[str, dict[str, str]]:
        from urllib.parse import parse_qs, urlsplit

        entry = next((row for row in self._catalog.entries if row.id == identity), None)
        if entry is None or not entry.selectable:
            raise SourceFailure("category_unavailable")
        parsed = urlsplit(entry.source_url)
        if parsed.path == "/marketplace/category/electronics/":
            return "category/electronics/", {}
        if identity.isdecimal():
            # The category link on the pt-BR source includes its label as well as the category ID.
            term = "Eletrônicos" if identity == "479353692612078" else entry.label
            return "search/", {"query": term, "category_id": identity}
        if parsed.path == f"/marketplace/category/{identity}/" and not parse_qs(parsed.query):
            return f"category/{identity}/", {}
        raise SourceFailure("category_route_unverified")

    def _context(self, rows: tuple["JsonObject", ...], query: Search) -> str | None:
        from garimpei.infra.gateway.listing.relay_parser import (
            browse_parameters,
            mapping,
            route_from,
        )

        self._source_context = None
        route = route_from(rows)
        params = mapping(route.get("params"))
        if not route:
            return "search_context_unverified"
        term = query.term + (" envio" if query.modality == "shipping" else "")
        if query.interest.kind == "product" and params.get("query") != term:
            return "wrong_search_query"
        category = params.get("category_id") or params.get("catFriendly")
        expected_category = query.interest.key
        if query.interest.kind == "category":
            category_route, _ = self._category(query.interest.key)
            if category_route.startswith("category/"):
                expected_category = category_route.split("/")[1]
            if category != expected_category:
                return "wrong_category_context"
        effective = browse_parameters(rows)
        self._native_sort = effective.get("commerce_search_sort_by") == "CREATION_TIME_DESCEND"
        latitude, longitude = (
            effective.get("filter_location_latitude"),
            effective.get("filter_location_longitude"),
        )
        observed_radius = effective.get("filter_radius_km")
        geo_verified = (
            self._origin is not None
            and isinstance(latitude, (int, float))
            and isinstance(longitude, (int, float))
            and observed_radius == (20 if query.modality == "pickup" else 500)
            and abs(latitude - self._origin.latitude) <= 0.0001
            and abs(longitude - self._origin.longitude) <= 0.0001
        )
        self._source_context = SearchContext(
            geo_verified,
            float(latitude) if isinstance(latitude, (int, float)) else None,
            float(longitude) if isinstance(longitude, (int, float)) else None,
            int(observed_radius) if isinstance(observed_radius, int) else None,
            str(params["query"]) if params.get("query") is not None else None,
        )
        if query.modality == "marketplace":
            return None
        radius = 20 if query.modality == "pickup" else 500
        if effective.get("filter_radius_km") != radius or self._origin is None:
            return "search_geography_unverified"
        latitude, longitude = (
            effective.get("filter_location_latitude"),
            effective.get("filter_location_longitude"),
        )
        if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
            return "search_geography_unverified"
        if (
            abs(latitude - self._origin.latitude) > 0.0001
            or abs(longitude - self._origin.longitude) > 0.0001
        ):
            return "wrong_search_geography"
        return None

    def detail(self, scope: Scope, external_id: str) -> Candidate:
        self._query_key = None
        from garimpei.domain.listing.listing import canonical_url
        from garimpei.infra.gateway.listing.relay_parser import listing_from

        rows, _ = self._browser.navigate(canonical_url(external_id))
        if any(row.get("_garimpei_unavailable_product_id") == external_id for row in rows):
            raise ListingUnavailable(external_id, "source_unavailable_product")
        matches = [
            row
            for row in rows
            if row.get("id") == external_id
            and "marketplace_listing_title" in row
            and "listing_price" in row
        ]
        if not matches:
            raise SourceFailure("listing_detail_unavailable")
        row = max(matches, key=lambda item: len(item)) | _verified_media_fields(rows, external_id)
        candidate = listing_from(row, detail=True)
        if candidate is None:
            raise SourceFailure("unverified_identity")
        return candidate

    def close(self) -> None:
        self._browser.close()


def _verified_media_fields(rows: tuple["JsonObject", ...], external_id: str) -> "JsonObject":
    # Marketplace sends the carousel in another fragment for the same verified listing ID.
    result: JsonObject = {}
    for row in rows:
        if row.get("id") != external_id:
            continue
        result.update(
            {
                key: row[key]
                for key in ("listing_photos", "primary_listing_photo")
                if row.get(key) is not None
            }
        )
    return result
