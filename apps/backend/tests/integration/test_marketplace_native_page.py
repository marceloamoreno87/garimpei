import json
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import parse_qs

import pytest

from garimpei.domain.listing.geography import Point
from garimpei.domain.listing.window import PublicationWindow
from garimpei.infra.gateway.listing.marketplace_browser import MarketplaceBrowser, SearchFilters
from garimpei.infra.gateway.listing.relay_parser import browse_parameters


def feed(identity: str, cursor: str | None) -> dict[str, object]:
    return {
        "marketplace_search": {
            "feed_units": {
                "edges": [
                    {"node": {"listing": {"id": identity, "marketplace_listing_title": "PS5"}}}
                ],
                "page_info": {"has_next_page": cursor is not None, "end_cursor": cursor},
            }
        }
    }


@pytest.mark.parametrize(
    "scenario",
    [
        "matching",
        "wrong_radius",
        "filtered_dates",
        "missing_context",
        "missing_feed",
        "wrong_origin",
        "background_feed",
        "active_window",
        "dates_unrequested",
    ],
)
def test_research_uses_only_matching_native_results_and_keeps_source_cursor(
    tmp_path: Path, scenario: str
) -> None:
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
    native: dict[str, object] = {
        "filter_radius_km": 500 if scenario == "wrong_radius" else 20,
        "filter_location_latitude": -23.9 if scenario == "wrong_origin" else -23.55,
        "filter_location_longitude": -46.6333,
    }
    if scenario == "filtered_dates":
        native["commerce_search_and_rp_ctime_days"] = "19000"
    if scenario == "missing_context":
        native = {}
    requests: list[dict[str, object]] = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            document = {
                "queryName": "CometMarketplaceSearchContentContainerQuery",
                "queryID": "synthetic-native-query",
                "variables": {"params": {"browse_request_params": native}},
                "data": {}
                if scenario in {"missing_feed", "background_feed"}
                else feed("101", "native-next"),
            }
            body = (
                '<script type="application/json">'
                + json.dumps(document)
                + "</script><script>window.require=name=>({token:'synthetic',USER_ID:'synthetic'});</script>"
                + (
                    "<script>fetch('/api/graphql/background',{method:'POST'})</script>"
                    if scenario == "background_feed"
                    else ""
                )
            ).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self) -> None:
            if self.path == "/api/graphql/background":
                body = json.dumps({"data": feed("301", None)}).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            fields = parse_qs(self.rfile.read(int(self.headers["Content-Length"])).decode())
            variables = json.loads(fields["variables"][0])
            requests.append(variables)
            body = json.dumps(
                {"data": feed("102" if variables.get("cursor") else "201", None)}
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, _format: str, *args: object) -> None:
            pass

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        browser = MarketplaceBrowser(state, 5, 100)
        try:
            rows, first = browser.search(
                f"http://127.0.0.1:{server.server_port}/search",
                SearchFilters(
                    Point(-23.55, -46.6333, None, "São Paulo", "SP"),
                    20,
                    PublicationWindow.ending_at(datetime(2026, 11, 13, tzinfo=UTC))
                    if scenario == "active_window"
                    else None,
                    scenario != "dates_unrequested",
                ),
            )
            assert first is not None
            unproved = any(row.get("_garimpei_response_context_unverified") is True for row in rows)
            if scenario != "matching":
                assert first.listings[0]["id"] == "201" and unproved
                assert browse_parameters(rows) == native
                return
            assert first.listings[0]["id"] == "101" and not unproved
            assert requests == []
            second = browser.continue_from("native-next")
            assert second.listings[0]["id"] == "102"
            assert len(requests) == 1 and requests[0]["cursor"] == "native-next"
            assert requests[0]["params"] == {"browse_request_params": native}
        finally:
            browser.close()
            server.shutdown()
            thread.join(timeout=5)
