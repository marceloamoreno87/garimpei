import fcntl
import json
import os
import re
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable
from urllib.parse import parse_qs, urlsplit

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    Response,
    sync_playwright,
)
from playwright.sync_api import Error as BrowserError
from playwright.sync_api import TimeoutError as BrowserTimeoutError
from playwright_stealth import Stealth

from garimpei.domain.listing.geography import Point
from garimpei.domain.listing.ports import SourceFailure
from garimpei.domain.listing.window import PublicationWindow
from garimpei.domain.robot.ports import RobotAdmission
from garimpei.infra.gateway.listing.relay_parser import (
    Feed,
    JsonObject,
    browse_parameters,
    documents,
    feed_from,
    mapping,
)
from garimpei.infra.gateway.robot.admission import robot_operation
from garimpei.infra.repository.integration.private_session import private_directory


def _native_research_matches(observed: JsonObject, filters: "SearchFilters") -> bool:
    if not filters.all_publication_dates or filters.window is not None:
        return False
    if observed.get("commerce_search_and_rp_ctime_days") not in (None, ""):
        return False
    latitude = observed.get("filter_location_latitude")
    longitude = observed.get("filter_location_longitude")
    radius = observed.get("filter_radius_km")
    return (
        isinstance(latitude, (int, float))
        and not isinstance(latitude, bool)
        and isinstance(longitude, (int, float))
        and not isinstance(longitude, bool)
        and type(radius) is int
        and radius == filters.radius_km
        and abs(latitude - filters.origin.latitude) <= 0.0001
        and abs(longitude - filters.origin.longitude) <= 0.0001
    )


def valid_source_cursor(cursor: str) -> bool:
    # Native end cursors are opaque strings, not necessarily base64. They are
    # returned only as JSON data; controls and unbounded input remain rejected.
    return re.fullmatch(r"[\x20-\x7e]{1,4096}", cursor) is not None


@dataclass(frozen=True)
class SearchFilters:
    origin: Point
    radius_km: int
    window: PublicationWindow | None
    all_publication_dates: bool = False


class MarketplaceNavigation(Protocol):
    def search(
        self, url: str, filters: SearchFilters
    ) -> tuple[tuple[JsonObject, ...], Feed | None]: ...
    def navigate(self, url: str) -> tuple[tuple[JsonObject, ...], Feed | None]: ...
    def scroll(self) -> Feed: ...
    def close(self) -> None: ...


@runtime_checkable
class MarketplaceContinuation(Protocol):
    def continue_from(self, cursor: str) -> Feed: ...


class MarketplaceBrowser:
    def __init__(
        self,
        state_path: Path,
        timeout: int,
        cadence_ms: int,
        *,
        profile: Path | None = None,
        login_origin: str = "https://www.facebook.com",
        profile_headless: bool = False,
        robot: RobotAdmission | None = None,
        sandbox: bool = False,
    ) -> None:
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="marketplace-browser")
        self._path = state_path
        self._profile, self._login_origin, self._profile_headless = (
            profile,
            login_origin,
            profile_headless,
        )
        self._robot = robot
        self._sandbox = sandbox
        self._timeout = timeout * 1000
        self._cadence = cadence_ms
        self._engine: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None
        self._feeds: list[Feed] = []
        self._lock_fd: int | None = None
        self._access_failure: SourceFailure | None = None
        self._filters: SearchFilters | None = None
        self._cursor: str | None = None
        self._query_payload: JsonObject | None = None
        self._detail_payload: JsonObject | None = None
        self._detail_origin: str | None = None

    def navigate(self, url: str) -> tuple[tuple[JsonObject, ...], Feed | None]:
        # Playwright's synchronous facade owns an event loop. Keep it off the
        # Django/ORM caller thread for the entire browser lifetime.
        return self._executor.submit(self._navigate, url).result()

    def search(
        self, url: str, filters: SearchFilters
    ) -> tuple[tuple[JsonObject, ...], Feed | None]:
        return self._executor.submit(self._search, url, filters).result()

    def scroll(self) -> Feed:
        return self._executor.submit(self._scroll).result()

    def continue_from(self, cursor: str) -> Feed:
        return self._executor.submit(self._continue_from, cursor).result()

    def _continue_from(self, cursor: str) -> Feed:
        # Only the opaque end cursor is restored; authenticated variables/tokens
        # are captured afresh by search() in this owned browser context.
        if self._query_payload is None or not valid_source_cursor(cursor):
            raise SourceFailure("cursor_expired")
        self._cursor = cursor
        return self._request_page()

    def close(self) -> None:
        try:
            self._executor.submit(self._close).result()
        finally:
            self._executor.shutdown(wait=True)

    def open_login(self) -> None:
        self._executor.submit(self._open_login).result()

    def _open_login(self) -> None:
        try:
            self._open().goto(self._login_origin + "/marketplace/", wait_until="domcontentloaded")
        except BrowserError:
            raise SourceFailure("browser_start_failed") from None

    def login_is_open(self) -> bool:
        return self._executor.submit(
            lambda: self._page is not None and not self._page.is_closed()
        ).result()

    def verify_login(self) -> bool:
        return self._executor.submit(self._verify_login).result()

    def _verify_login(self) -> bool:
        try:
            page = self._open()
            page.goto(self._login_origin + "/marketplace/", wait_until="domcontentloaded")
            self._check_access(page)
            user = page.evaluate(
                "() => {try {return require('CurrentUserInitialData').USER_ID;} catch {return null;}}"
            )
            cookies = page.context.cookies(self._login_origin)
            return isinstance(user, str) and any(
                item["name"] == "c_user"
                and item["value"] == user
                and user.isdecimal()
                and int(user) > 0
                for item in cookies
            )
        except (BrowserError, SourceFailure):
            return False

    def _open(self) -> Page:
        if self._page is not None:
            return self._page
        try:
            self._acquire_session()
        except SourceFailure as failure:
            self._close()
            self._access_failure = failure
            raise
        try:
            self._engine = sync_playwright().start()
            if self._profile is not None:
                self._context = self._engine.chromium.launch_persistent_context(
                    self._profile,
                    timeout=self._timeout,
                    headless=self._profile_headless,
                    chromium_sandbox=self._sandbox,
                    locale="pt-BR",
                    timezone_id="America/Sao_Paulo",
                    no_viewport=True,
                    accept_downloads=False,
                )
                self._page = (
                    self._context.pages[0] if self._context.pages else self._context.new_page()
                )
                self._page.set_default_timeout(self._timeout)
                self._page.on("response", self._receive)
                return self._page
            Stealth(
                navigator_languages_override=("pt-BR", "pt", "en-US", "en"),
                navigator_platform=False,
                navigator_platform_override=None,
                webgl_vendor=False,
            ).hook_playwright_context(self._engine)
            self._browser = self._engine.chromium.launch(
                headless=True,
                chromium_sandbox=self._sandbox,
                timeout=self._timeout,
                args=["--disable-blink-features=AutomationControlled"],
                ignore_default_args=["--enable-automation"],
            )
            self._context = self._browser.new_context(
                storage_state=self._path,
                locale="pt-BR",
                timezone_id="America/Sao_Paulo",
                viewport={"width": 1357, "height": 1271},
                color_scheme="light",
                reduced_motion="reduce",
                accept_downloads=False,
            )
            self._page = self._context.new_page()
            self._page.set_default_timeout(self._timeout)
            self._page.on("response", self._receive)
            return self._page
        except Exception:
            self._close()
            raise SourceFailure("browser_start_failed") from None

    def _acquire_session(self) -> None:
        if self._profile is not None:
            private_directory(self._profile.parent)
            private_directory(self._profile)
        self._lock_fd = os.open(self._path.with_suffix(".lock"), os.O_CREAT | os.O_RDWR, 0o600)
        deadline = time.monotonic() + self._timeout / 1000
        while time.monotonic() < deadline:
            try:
                fcntl.flock(self._lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return
            except BlockingIOError:
                time.sleep(0.1)
        raise SourceFailure("browser_session_in_use", 30)

    def _receive(self, response: Response) -> None:
        if "/api/graphql" not in response.url or response.status != 200:
            return
        try:
            feed = feed_from(documents(response.text()))
        except BrowserError:
            return
        if feed is not None:
            self._feeds.append(feed)

    def _navigate(self, url: str) -> tuple[tuple[JsonObject, ...], Feed | None]:
        if not re.fullmatch(r"/marketplace/item/[0-9]+/?", urlsplit(url).path):
            return self._read_page(url)
        search = self._query_payload, self._cursor, self._filters
        try:
            return self._read_page(url)
        finally:
            # Detail enrichment may navigate away, but pagination belongs to the search
            # captured before it. The authenticated context can continue that request.
            self._query_payload, self._cursor, self._filters = search

    def _read_page(self, url: str) -> tuple[tuple[JsonObject, ...], Feed | None]:
        if self._access_failure is not None:
            raise self._access_failure
        started = time.monotonic()
        parsed = urlsplit(url)
        target = re.fullmatch(r"/marketplace/item/([0-9]+)/?", parsed.path)
        if target and self._detail_payload and self._detail_origin == parsed.netloc:
            variables = mapping(self._detail_payload["variables"]).copy()
            variables["targetId"] = target.group(1)
            payload = self._detail_payload | {"variables": variables}
            rows = self._query_rows(payload)
            if _has_listing_gallery(rows, target.group(1)) and any(
                row.get("id") == target.group(1) and "listing_price" in row for row in rows
            ):
                return rows, None
        page = self._open()
        try:
            self._feeds.clear()
            self._filters = None
            self._cursor = None
            self._query_payload = None
            page.wait_for_timeout(self._cadence)
            remaining = self._timeout - int((time.monotonic() - started) * 1000)
            if remaining <= 0:
                raise SourceFailure("source_request_timeout")
            response = self._goto(page, url, remaining)
            if response is not None and response.status in (401, 403, 429):
                raise SourceFailure(
                    f"source_http_{response.status}",
                    300,
                    access=response.status != 429,
                )
            page.wait_for_timeout(self._cadence)
            self._check_access(page)
            rows = tuple(
                row
                for payload in page.locator('script[type="application/json"]').all_text_contents()
                for row in documents(payload)
            )
            if target:
                self._remember_detail(rows, parsed.netloc)
            if target and parse_qs(urlsplit(page.url).query).get("unavailable_product") == ["1"]:
                rows += ({"_garimpei_unavailable_product_id": target.group(1)},)
            return rows, feed_from(rows) or (self._feeds[-1] if self._feeds else None)
        except SourceFailure as failure:
            if failure.access:
                self._access_failure = failure
            raise
        except BrowserError as error:
            raise self._browser_failure(page, error, "source_navigation_failed") from None

    def _search(
        self,
        url: str,
        filters: SearchFilters,
    ) -> tuple[tuple[JsonObject, ...], Feed | None]:
        rows, _ = self._navigate(url)
        self._filters = filters
        self._cursor = None
        self._query_payload = self._query_template(rows)
        native_feed = feed_from(rows)
        if native_feed is not None and _native_research_matches(browse_parameters(rows), filters):
            # These results and metadata came from the same native document. A
            # rewritten POST would discard that binding without proving its own.
            self._cursor = native_feed.cursor
            return rows, native_feed
        variables = deepcopy(mapping(self._query_payload["variables"]))
        original = variables.get("params")
        parsed = mapping(json.loads(original)) if isinstance(original, str) else mapping(original)
        browse = mapping(parsed.get("browse_request_params"))
        self._patch_filters(browse)
        parsed["browse_request_params"] = browse
        variables["params"] = json.dumps(parsed) if isinstance(original, str) else parsed
        variables["buyLocation"] = {
            "latitude": filters.origin.latitude,
            "longitude": filters.origin.longitude,
        }
        self._query_payload["variables"] = variables
        feed = self._request_page()
        # Original native metadata is observed evidence. Patched request filters are not proof
        # that the source applied them and must never be spliced into those observations.
        return rows + ({"_garimpei_response_context_unverified": True},), feed

    @staticmethod
    def _query_template(
        rows: tuple[JsonObject, ...], name: str = "CometMarketplaceSearchContentContainerQuery"
    ) -> JsonObject:
        for row in rows:
            if row.get("queryName") == name:
                return {
                    "doc_id": row["queryID"],
                    "name": row["queryName"],
                    "variables": mapping(row.get("variables")).copy(),
                }
        raise SourceFailure("search_query_template_unavailable")

    def _remember_detail(self, rows: tuple[JsonObject, ...], origin: str) -> None:
        try:
            payload = self._query_template(rows, "MarketplacePDPContainerQuery")
        except SourceFailure:
            return
        self._detail_payload, self._detail_origin = payload, origin

    def _request_page(self) -> Feed:
        assert self._query_payload is not None
        variables = mapping(self._query_payload["variables"])
        variables["cursor"] = self._cursor
        self._query_payload["variables"] = variables
        rows = self._query_rows(self._query_payload)
        feed = feed_from(rows)
        if feed is None:
            raise SourceFailure("search_query_unavailable")
        self._cursor = feed.cursor
        return feed

    def _query_rows(self, query: JsonObject) -> tuple[JsonObject, ...]:
        page = self._open()
        try:
            payload = self._evaluate_query(page, query)
            page.wait_for_timeout(self._cadence)
            self._check_access(page)
            result = mapping(payload)
            status = result.get("status")
            if isinstance(status, int) and status != 200:
                retry = str(result.get("retryAfter", ""))
                default_delay = 300 if status in (401, 403, 429) else 0
                delay = (
                    int(retry)
                    if retry.isascii() and retry.isdecimal() and len(retry) < 8
                    else default_delay
                )
                raise SourceFailure(
                    f"source_http_{status}",
                    max(1, delay) if status == 429 else delay,
                    access=status in (401, 403),
                )
            body = result.get("body")
            return documents(body) if isinstance(body, str) else ()
        except SourceFailure as failure:
            if failure.access:
                self._access_failure = failure
            raise
        except BrowserError as error:
            raise self._browser_failure(page, error, "search_query_failed") from None

    def _goto(self, page: Page, url: str, timeout: int) -> Response | None:
        with robot_operation(self._robot, "source_browser", "navigate:" + url):
            return page.goto(url, wait_until="domcontentloaded", timeout=timeout)

    def _evaluate_query(self, page: Page, query: JsonObject) -> JsonObject:
        request = json.dumps(query, sort_keys=True, separators=(",", ":"))
        with robot_operation(self._robot, "source_browser", "query:" + request):
            return mapping(
                page.evaluate(
                    """async input => {
                  const controller = new AbortController();
                  const timer = setTimeout(() => controller.abort(), input.timeout);
                  try {
                    const requireModule = name => {
                      try { return require(name); } catch { return {}; }
                    };
                    const token = requireModule('DTSGInitialData').token || requireModule('DTSG').getToken?.();
                    const lsd = requireModule('LSD').token;
                    const user = requireModule('CurrentUserInitialData').USER_ID;
                    if (!token || !user) return '';
                    const body = new URLSearchParams({
                      av:user, __user:user, __a:'1', __comet_req:'15', fb_dtsg:token, lsd:lsd || '',
                      fb_api_caller_class:'RelayModern',
                      fb_api_req_friendly_name:input.query.name,
                      doc_id:input.query.doc_id,
                      variables:JSON.stringify(input.query.variables),
                      server_timestamps:'true'
                    });
                    const response = await fetch('/api/graphql/', {
                      method:'POST', credentials:'same-origin', signal:controller.signal,
                      headers:{'Content-Type':'application/x-www-form-urlencoded'}, body
                    });
                    return {status:response.status, retryAfter:response.headers.get('Retry-After') || '', body:response.ok ? await response.text() : ''};
                  } finally { clearTimeout(timer); }
                }""",
                    {"query": query, "timeout": self._timeout},
                )
            )

    def _browser_failure(self, page: Page, error: BrowserError, fallback: str) -> SourceFailure:
        if page.is_closed():
            failure = SourceFailure("browser_session_closed", access=True)
            self._access_failure = failure
            return failure
        message = str(error)
        if isinstance(error, BrowserTimeoutError) or "AbortError" in message:
            return SourceFailure("source_request_timeout")
        if "Failed to fetch" in message or "net::ERR_" in message:
            return SourceFailure("source_network_failed")
        if "Execution context was destroyed" in message:
            return SourceFailure("source_context_changed", 15)
        return SourceFailure(fallback)

    def _patch_filters(self, browse: JsonObject) -> None:
        filters = self._filters
        assert filters is not None
        browse.update(
            {
                "filter_location_latitude": filters.origin.latitude,
                "filter_location_longitude": filters.origin.longitude,
                "filter_radius_km": filters.radius_km,
                "commerce_search_sort_by": "CREATION_TIME_DESCEND",
                "commerce_enable_local_pickup": True,
                "commerce_enable_shipping": True,
            }
        )
        if filters.all_publication_dates:
            browse.pop("commerce_search_and_rp_ctime_days", None)
        if filters.window is not None:
            first = int(filters.window.start.timestamp()) // 86400 - 1
            last = int(filters.window.end.timestamp()) // 86400 + 1
            # Request a calendar-day superset, then apply exact UTC limits in the domain.
            browse["commerce_search_and_rp_ctime_days"] = ";".join(
                str(day) for day in range(last, first - 1, -1)
            )

    def _check_access(self, page: Page) -> None:
        if any(fragment in page.url for fragment in ("/checkpoint", "/login", "/challenge")):
            raise SourceFailure("session_challenge", access=True)
        if page.locator('input[name="email"],input[name="pass"]').count():
            raise SourceFailure("session_expired", access=True)
        cookies = self._context.cookies(self._login_origin) if self._context else []
        names = {cookie["name"] for cookie in cookies}
        if not {"c_user", "xs"} <= names:
            raise SourceFailure("session_expired", access=True)

    def _scroll(self) -> Feed:
        if self._query_payload is not None:
            return self._request_page()
        page = self._open()
        start = len(self._feeds)
        try:
            self._scroll_request(page)
            page.wait_for_timeout(self._cadence)
            self._check_access(page)
            if len(self._feeds) <= start:
                raise SourceFailure("continuation_unavailable")
            return self._feeds[-1]
        except BrowserError:
            raise SourceFailure("continuation_unavailable") from None

    def _scroll_request(self, page: Page) -> None:
        with robot_operation(self._robot, "source_browser", "scroll:" + page.url):
            with page.expect_response(
                lambda response: (
                    "/api/graphql" in response.url
                    and "MarketplaceSearch" in (response.request.post_data or "")
                ),
                timeout=self._timeout,
            ):
                page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")

    def _close(self) -> None:
        try:
            self._save_state()
        finally:
            self._close_browser()

    def _save_state(self) -> None:
        if self._profile is not None:
            return
        if self._context is None:
            return
        names = {cookie["name"] for cookie in self._context.cookies("https://www.facebook.com")}
        if not {"c_user", "xs"} <= names:
            return
        with tempfile.NamedTemporaryFile("w", dir=self._path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(self._context.storage_state(), handle)
        temporary.chmod(0o600)
        temporary.replace(self._path)

    def _close_browser(self) -> None:
        try:
            if self._profile is not None and self._context is not None:
                self._context.close()
            if self._browser is not None:
                self._browser.close()
            if self._engine is not None:
                self._engine.stop()
        finally:
            self._page = None
            self._context = None
            self._browser = None
            self._engine = None
            if self._lock_fd is not None:
                os.close(self._lock_fd)
                self._lock_fd = None


def _has_listing_gallery(rows: tuple[JsonObject, ...], identity: str) -> bool:
    return any(
        row.get("id") == identity and _recognized_gallery(row.get("listing_photos")) for row in rows
    )


def _recognized_gallery(value: object) -> bool:
    return isinstance(value, list) or (
        isinstance(value, dict) and isinstance(value.get("nodes"), list)
    )
