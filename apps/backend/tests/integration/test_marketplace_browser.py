import fcntl
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread, Timer
from urllib.parse import parse_qs, urlsplit

import pytest
from django.utils.asyncio import async_unsafe

from garimpei.domain.listing.ports import SourceFailure
from garimpei.infra.gateway.listing.marketplace_browser import MarketplaceBrowser


def test_browser_navigation_keeps_django_sync_io_and_consistent_stealth(tmp_path: Path) -> None:
    state = tmp_path / "state.json"
    state.write_text(
        json.dumps(
            {
                "cookies": [
                    {
                        "name": name,
                        "value": "synthetic",
                        "domain": ".facebook.com",
                        "path": "/",
                        "expires": -1,
                        "httpOnly": True,
                        "secure": True,
                        "sameSite": "Lax",
                    }
                    for name in ("c_user", "xs")
                ],
                "origins": [],
            }
        )
    )
    state.chmod(0o600)
    headers: list[dict[str, str]] = []
    fingerprints: list[dict[str, object]] = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            headers.append(
                {
                    "user_agent": self.headers.get("User-Agent", ""),
                    "client_hints": self.headers.get("Sec-CH-UA", ""),
                }
            )
            url = urlsplit(self.path)
            if url.path == "/fingerprint":
                fingerprints.append(json.loads(parse_qs(url.query)["data"][0]))
            data = b"""<!doctype html><script>
fetch('/fingerprint?data='+encodeURIComponent(JSON.stringify({
 webdriver:navigator.webdriver,
 user_agent:navigator.userAgent,
 platform:navigator.platform,
 ua_platform:navigator.userAgentData?.platform,
 language:navigator.language,
 timezone:Intl.DateTimeFormat().resolvedOptions().timeZone
})));
</script>"""
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, _format: str, *args: object) -> None:
            pass

    @async_unsafe
    def django_sync_boundary() -> str:
        return "Django synchronous database operations are allowed"

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        worker = Thread(target=server.serve_forever, daemon=True)
        worker.start()
        browser = MarketplaceBrowser(state, 5, 500)
        held = os.open(state.with_suffix(".lock"), os.O_CREAT | os.O_RDWR, 0o600)
        fcntl.flock(held, fcntl.LOCK_EX)
        release = Timer(0.25, lambda: os.close(held))
        release.start()
        try:
            browser.navigate(f"http://127.0.0.1:{server.server_port}/")
            assert django_sync_boundary() == "Django synchronous database operations are allowed"
            assert fingerprints
            fingerprint = fingerprints[0]
            assert fingerprint["webdriver"] is False
            assert fingerprint["language"] == "pt-BR"
            assert fingerprint["timezone"] == "America/Sao_Paulo"
            assert (
                fingerprint["platform"] == "Linux x86_64" and fingerprint["ua_platform"] == "Linux"
            )
            assert all(
                "HeadlessChrome" not in row["user_agent"] + row["client_hints"] for row in headers
            )
            assert headers[0]["user_agent"] == fingerprint["user_agent"]

            def close_window() -> None:
                assert browser._page is not None
                browser._page.close()

            browser._executor.submit(close_window).result()
            with pytest.raises(SourceFailure) as closed:
                browser.navigate(f"http://127.0.0.1:{server.server_port}/")
            assert closed.value.reason == "browser_session_closed" and closed.value.access

        finally:
            release.join()
            browser.close()
            server.shutdown()
            worker.join()


def test_browser_search_applies_effective_filters_and_uses_server_cursor(tmp_path: Path) -> None:
    from datetime import UTC, datetime
    from urllib.parse import parse_qs

    from garimpei.domain.listing.geography import Point
    from garimpei.domain.listing.window import PublicationWindow
    from garimpei.infra.gateway.listing.marketplace_browser import SearchFilters

    state = tmp_path / "session.json"
    state.write_text(
        json.dumps(
            {
                "cookies": [
                    {
                        "name": name,
                        "value": "synthetic",
                        "domain": ".facebook.com",
                        "path": "/",
                        "expires": -1,
                        "httpOnly": True,
                        "secure": True,
                        "sameSite": "Lax",
                    }
                    for name in ("c_user", "xs")
                ],
                "origins": [],
            }
        )
    )
    state.chmod(0o600)
    requests: list[dict[str, object]] = []
    response_status = [200]
    navigated: list[str] = []
    template = {
        "queryName": "CometMarketplaceSearchContentContainerQuery",
        "queryID": "synthetic-query",
        "variables": {"params": {"browse_request_params": {"filter_radius_km": 6}}},
    }

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            navigated.append(self.path)
            if self.path == "/marketplace/item/104/":
                self.send_response(302)
                self.send_header("Location", "/marketplace/?unavailable_product=1")
                self.end_headers()
                return
            current = template
            if self.path.startswith("/marketplace/item/"):
                current = {
                    "queryName": "MarketplacePDPContainerQuery",
                    "queryID": "synthetic-detail",
                    "variables": {"targetId": self.path.strip("/").split("/")[-1]},
                    "listing": {
                        "id": self.path.strip("/").split("/")[-1],
                        "marketplace_listing_title": "PlayStation 5",
                        "listing_price": {"amount": "2200.00", "currency": "BRL"},
                    },
                }
            html = (
                '<script type="application/json">' + json.dumps(current) + "</script>"
                '<script>window.require=name=>({token:"synthetic",USER_ID:"synthetic"});</script>'
            ).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)

        def do_POST(self) -> None:
            data = parse_qs(self.rfile.read(int(self.headers["Content-Length"])).decode())
            assert data["__comet_req"] == ["15"]
            variables = json.loads(data["variables"][0])
            requests.append(variables)
            if response_status[0] != 200:
                self.send_response(response_status[0])
                self.send_header("Retry-After", "7")
                self.end_headers()
                self.wfile.write(b"{}")
                return
            if "targetId" in variables:
                body = json.dumps(
                    {
                        "data": {
                            "listing": {
                                "id": variables["targetId"],
                                **(
                                    {"listing_photos": []} if variables["targetId"] == "102" else {}
                                ),
                                "marketplace_listing_title": "PlayStation 5",
                                "listing_price": {"amount": "2200.00", "currency": "BRL"},
                            }
                        }
                    }
                ).encode()
                if variables["targetId"] in {"103", "104"}:
                    body = b'{"data":{"node":null}}'
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            second = variables.get("cursor") == "next"
            body = json.dumps(
                {
                    "data": {
                        "marketplace_search": {
                            "feed_units": {
                                "edges": [
                                    {
                                        "node": {
                                            "listing": {
                                                "id": "102" if second else "101",
                                                "marketplace_listing_title": "PlayStation 5",
                                            }
                                        }
                                    }
                                ],
                                "page_info": {
                                    "has_next_page": not second,
                                    "end_cursor": None if second else "next",
                                },
                            }
                        }
                    }
                }
            ).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, _format: str, *args: object) -> None:
            pass

    window = PublicationWindow.ending_at(datetime(2026, 11, 11, 12, tzinfo=UTC))
    origin = Point(-23.55, -46.63, None, "São Paulo", "SP")
    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        worker = Thread(target=server.serve_forever, daemon=True)
        worker.start()
        browser = MarketplaceBrowser(state, 5, 500)
        try:
            observed_rows, first = browser.search(
                f"http://127.0.0.1:{server.server_port}/",
                SearchFilters(origin, 20, window),
            )
            from garimpei.infra.gateway.listing.relay_parser import browse_parameters

            assert browse_parameters(observed_rows) == {"filter_radius_km": 6}
            assert any(
                row.get("_garimpei_response_context_unverified") is True for row in observed_rows
            )
            # Detail navigation must preserve the pending search cursor and native request.
            browser.navigate(f"http://127.0.0.1:{server.server_port}/marketplace/item/101/")
            second = browser.scroll()
            assert first is not None and first.listings[0]["id"] == "101"
            assert second.listings[0]["id"] == "102"
            assert [request["cursor"] for request in requests if "cursor" in request] == [
                None,
                "next",
            ]
            params = requests[0]["params"]
            assert isinstance(params, dict)
            filters = params["browse_request_params"]
            assert filters["filter_radius_km"] == 20
            assert filters["filter_location_latitude"] == origin.latitude
            assert filters["filter_location_longitude"] == origin.longitude
            assert filters["commerce_search_sort_by"] == "CREATION_TIME_DESCEND"
            days = set(map(int, filters["commerce_search_and_rp_ctime_days"].split(";")))
            assert int(window.start.timestamp()) // 86400 in days
            assert int(window.end.timestamp()) // 86400 in days
            base_url = f"http://127.0.0.1:{server.server_port}"
            browser.navigate(base_url + "/marketplace/item/101/")
            rows, _ = browser.navigate(base_url + "/marketplace/item/102/")
            assert any(row.get("id") == "102" and "listing_price" in row for row in rows)
            assert requests[-1]["targetId"] == "102"
            assert "/marketplace/item/101/" in navigated
            assert "/marketplace/item/102/" not in navigated
            rows, _ = browser.navigate(base_url + "/marketplace/item/105/")
            assert "/marketplace/item/105/" in navigated
            rows, _ = browser.navigate(base_url + "/marketplace/item/103/")
            assert any(row.get("id") == "103" and "listing_price" in row for row in rows)
            assert "/marketplace/item/103/" in navigated
            rows, _ = browser.navigate(base_url + "/marketplace/item/104/")
            assert {"_garimpei_unavailable_product_id": "104"} in rows
            import pytest

            from garimpei.domain.listing.ports import SourceFailure

            response_status[0] = 429
            with pytest.raises(SourceFailure) as rate:
                browser.navigate(base_url + "/marketplace/item/105/")
            assert rate.value.reason == "source_http_429" and rate.value.retry_after == 7
            assert not rate.value.access
            response_status[0] = 403
            with pytest.raises(SourceFailure) as denied:
                browser.navigate(base_url + "/marketplace/item/106/")
            assert denied.value.access
            before = len(requests)
            with pytest.raises(SourceFailure):
                browser.navigate(base_url + "/marketplace/item/107/")
            assert len(requests) == before
        finally:
            browser.close()
            server.shutdown()
            worker.join()
