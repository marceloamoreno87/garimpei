"""Measure existing adapters at their real timeout boundary, using loopback only."""

import json
import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

from garimpei.domain.alert.alert import AlertPolicy, Binding, Delivery
from garimpei.domain.listing.listing import Match
from garimpei.domain.listing.ports import SourceFailure
from garimpei.domain.listing.scope import Scope, Search
from garimpei.domain.valuation.ports import NewSourceFailure
from garimpei.infra.gateway.alert.waha_gateway import WahaGateway
from garimpei.infra.gateway.listing.fixture_source import FixtureSource
from garimpei.infra.gateway.valuation.new_source import RetailNewSource
from tests.factories.runtime import FoundationInstance


@contextmanager
def delayed_origin(delay: float) -> Iterator[str]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.answer()

        def do_POST(self) -> None:
            self.answer()

        def answer(self) -> None:
            time.sleep(delay)
            parameters = {
                key: values[0]
                for key, values in parse_qs(
                    urlsplit(self.path).query, keep_blank_values=True
                ).items()
            }
            body: dict[str, object] = {"offers": []}
            if self.path.startswith("/search"):
                body = {
                    "context": {key: value for key, value in parameters.items() if key != "page"},
                    "cards": [],
                    "next": None,
                    "end": True,
                    "empty": True,
                }
            if self.command == "POST":
                request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                body = {
                    "id": "synthetic-calibration",
                    "fromMe": True,
                    "to": request["chatId"],
                    "from": "200@c.us",
                    "body": request["text"],
                    "ack": 1,
                }
            payload = json.dumps(body).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            try:
                self.wfile.write(payload)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def log_message(self, _format: str, *_args: object) -> None:
            pass

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        server.daemon_threads = True
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}"
        finally:
            server.shutdown()
            thread.join()


def _probe(stage: str, url: str) -> str:
    if stage == "valuation":
        RetailNewSource(Path("unused"), url, timeout=30).offers("synthetic", datetime.now(UTC))
        return "quotes_returned"
    if stage == "channel":
        delivery = Delivery(
            uuid4(),
            1,
            Binding("synthetic", "100@c.us", "200@c.us"),
            "Synthetic calibration",
            datetime.now(UTC),
            None,
            False,
        )
        return WahaGateway(url, "synthetic-only", AlertPolicy()).send(delivery).state
    scope = Scope(uuid4(), "facebook_marketplace", "01001000", 1, "synthetic", ())
    FixtureSource(url, 20).search(
        scope, Search(Match("product", "synthetic"), "synthetic", "marketplace"), None
    )
    return "page_returned"


def measure_adapters(instance: FoundationInstance) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for stage, timeout in (("source", 20), ("valuation", 30), ("channel", 10)):
        rows.extend(_measure(stage, timeout, instance))
    return rows


def _measure(stage: str, timeout: int, instance: FoundationInstance) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for fault in (False, True):
        with delayed_origin(timeout + 1 if fault else 0) as url:
            for repetition in range(5):
                started = time.monotonic()
                outcome = "returned"
                try:
                    outcome = _probe(stage, url)
                except (SourceFailure, NewSourceFailure):
                    outcome = "controlled_failure"
                elapsed = time.monotonic() - started
                with instance.database() as database:
                    row = database.execute(
                        "SELECT count(*) FROM procrastinate_jobs WHERE status IN ('todo','doing')"
                    ).fetchone()
                rows.append(
                    {
                        "stage": stage,
                        "case": "timeout" if fault else "control",
                        "repetition": repetition + 1,
                        "seconds": elapsed,
                        "timeout_seconds": timeout,
                        "outcome": outcome,
                        "pending_jobs": int(str(row[0])) if row else 0,
                    }
                )
    return rows
