import json
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Event, Thread
from typing import Any, cast
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

from tests.factories.runtime import FoundationInstance, prepare_instance

DATA = cast(
    dict[str, Any],
    json.loads((Path(__file__).parents[1] / "fixtures/listing/marketplace.json").read_text()),
)
CATEGORY: str = DATA["categories"]["electronics"]
PRODUCT: str = DATA["product"]
CEP: str = DATA["reference_cep"]
OTHER_CEP: str = DATA["other_cep"]
CATEGORIES = (CATEGORY, "cameras")


@dataclass
class Source:
    mode: str = "initial"
    price: str | None = "R$ 2.300,00"
    calls: list[tuple[str, dict[str, str]]] = field(default_factory=list)
    pause_path: str | None = None
    pause_term: str | None = None
    held: Event = field(default_factory=Event)
    release: Event = field(default_factory=Event)

    def respond(self, path: str, parameters: dict[str, str]) -> tuple[int, dict[str, object]]:
        mode, price = self.mode, self.price
        self.calls.append((path, parameters.copy()))
        if path == self.pause_path and (
            self.pause_term is None or parameters.get("term") == self.pause_term
        ):
            self.pause_path = None
            self.held.set()
            self.release.wait(12)
        if path == "/cep":
            return 200, {
                "cep": parameters["cep"],
                "point": DATA["geocoding"].get(parameters["cep"]),
            }
        if path.startswith("/detail/"):
            return self._detail(path.removeprefix("/detail/"), parameters["cep"], mode, price)
        return self._search(parameters, mode, price)

    def _detail(
        self, identity: str, cep: str, mode: str, price: str | None
    ) -> tuple[int, dict[str, object]]:
        if mode == "many_details_down":
            return 503, {}
        if mode == "withdrawn" and identity in {"101", "103"}:
            return 200, {
                "url": f"https://www.facebook.com/marketplace/item/{identity}/",
                "unavailable": True,
                "context_cep": cep,
            }
        if mode in {"partial", "fresh_partial"} and identity == "102":
            return 503, {}
        if mode in {"window", "window_revisit"} and identity in {"107", "108", "109", "110"}:
            return 200, self._window_card(identity) | {"context_cep": cep}
        if mode == "many" and identity.startswith("2"):
            row = self._many_card(identity)
        else:
            row = dict(DATA["details"][identity])
        if mode == "edited" and identity == "106":
            row["title"] = "Notebook recuperado"
            row["published_at"] = "2026-01-01T12:00:00+00:00"
        if identity == "101":
            row["price"] = price
            if mode == "missing":
                row = {key: row[key] for key in ("url", "title")}
        if mode == "fresh_partial":
            row["published_at"] = "2026-01-01T12:00:30+00:00"
        return 200, row | {"context_cep": cep}

    def _search(
        self, parameters: dict[str, str], mode: str, price: str | None
    ) -> tuple[int, dict[str, object]]:
        context = parameters.copy()
        page = context.pop("page")
        term = context["term"]
        continuation = None
        if mode in {"access", "limited"} and term == PRODUCT:
            return (403 if mode == "access" else 429), {}
        if mode in {"partial", "fresh_partial"} and term == CATEGORY and page:
            return 503, {}
        if mode == "wrong_context" and term == PRODUCT:
            context["territory"] = "foreign"
        if mode == "fresh_partial":
            cards = [dict(DATA["cards"]["101"]) | {"published_at": "2026-01-01T12:00:30+00:00"}]
            if term == CATEGORY:
                continuation = "second"
            elif term == "cameras":
                cards = []
            else:
                cards = [dict(DATA["cards"]["103"]) | {"published_at": "2026-01-01T12:00:30+00:00"}]
        elif mode == "window":
            cards = [
                self._window_card(identity)
                for identity in (("108", "109", "110") if page else ("107",))
            ]
            continuation = None if page else "second"
        elif mode in {"many", "many_details_down"} and term == CATEGORY:
            cards = [self._many_card(str(200 + i)) for i in range(25)]
        else:
            identities, continuation = self._ids(term, page, mode)
            cards = [dict(DATA["cards"].get(x) or DATA["details"][x]) for x in identities]
        for card in cards:
            link = str(card["url"])
            if mode == "edited" and "/106/" in link:
                card["title"] = "Notebook recuperado"
                card["published_at"] = "2026-01-01T12:00:00+00:00"
            if "/101/" in link:
                card["price"] = price
                if page:
                    card["url"] = link + "?tracking=fixture"
        return 200, {
            "context": context,
            "cards": cards,
            "next": continuation,
            "end": continuation is None,
            "empty": not cards,
        }

    @staticmethod
    def _ids(term: str, page: str, mode: str) -> tuple[tuple[str, ...], str | None]:
        if mode in {"empty", "many", "many_details_down", "window_revisit", "withdrawn"}:
            return (), None
        if mode in {"recovery", "missing", "edited"}:
            return (("106",) if term in {PRODUCT, "Notebook"} else ()), None
        if term == CATEGORY:
            if not page:
                return ("101",), "second"
            return (("101", "105") if mode != "repeated" else ("101",)), None
        if term == "cameras":
            return ("102",), None
        if term == PRODUCT:
            return ("101", "103", "104"), None
        return (), None

    @staticmethod
    def _window_card(identity: str) -> dict[str, object]:
        dates = {
            "107": "2025-12-30T11:59:59+00:00",
            "108": "2025-12-30T12:00:00+00:00",
            "109": "2026-01-01T12:00:01+00:00",
            "110": "2026-01-01T12:00:00+00:00",
        }
        return {
            "url": f"https://www.facebook.com/marketplace/item/{identity}/",
            "title": "PlayStation 5",
            "price": "R$ 2.200,00",
            "published_at": dates[identity],
            "shipping_offered": True,
            "shipping_evidence": "source_delivery_types",
        }

    @staticmethod
    def _many_card(identity: str) -> dict[str, object]:
        return {"url": f"https://www.facebook.com/marketplace/item/{identity}/", "title": "Teste"}


@contextmanager
def serve(source: Source) -> Iterator[str]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            url = urlsplit(self.path)
            parameters = {
                key: value[0] for key, value in parse_qs(url.query, keep_blank_values=True).items()
            }
            status, body = source.respond(url.path, parameters)
            data = json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            if status == 429:
                self.send_header("Retry-After", "90")
            self.end_headers()
            try:
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def log_message(self, _format: str, *args: object) -> None:
            pass

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}"
        finally:
            source.release.set()
            server.shutdown()
            thread.join()


@dataclass
class ControlledClock:
    path: Path
    value: datetime = datetime(2026, 1, 1, 12, tzinfo=UTC)

    def advance(self, seconds: int) -> None:
        self.value += timedelta(seconds=seconds)
        replacement = self.path.with_suffix(".new")
        replacement.write_text(self.value.isoformat())
        replacement.replace(self.path)


def prepare_listing_instance(
    root: Path, private: Path, url: str
) -> tuple[FoundationInstance, ControlledClock]:
    instance = prepare_instance(root, private, "f04_" + uuid4().hex[:10])
    clock = ControlledClock(private / "clock")
    clock.advance(0)
    with instance.private_file.open("a") as file:
        file.write(
            f"GARIMPEI_LISTING_FIXTURE_URL={url}\n"
            f"GARIMPEI_LISTING_FIXTURE_CLOCK={clock.path}\n"
            "GARIMPEI_LISTING_INTERVAL=60\nGARIMPEI_LISTING_TIMEOUT=15\n"
            "GARIMPEI_LISTING_LEASE=20\nGARIMPEI_LISTING_RETRY_BASE=5\n"
        )
    return instance, clock


@dataclass
class ConditionSource(Source):
    """F05 evidence enters the real F04 worker through its loopback source port."""

    rows: dict[str, dict[str, Any]] = field(default_factory=dict)
    failed: bool = False

    def __post_init__(self) -> None:
        self.rows = json.loads(
            (Path(__file__).parents[1] / "fixtures/listing/condition_cases.json").read_text()
        )

    def respond(self, path: str, parameters: dict[str, str]) -> tuple[int, dict[str, object]]:
        self.calls.append((path, parameters.copy()))
        if path == self.pause_path:
            self.pause_path = None
            self.held.set()
            self.release.wait(12)
        if path == "/cep":
            return 200, {"cep": parameters["cep"], "point": DATA["geocoding"][CEP]}
        if self.failed:
            return 503, {}
        if path.startswith("/detail/"):
            identity = path.removeprefix("/detail/")
            row = next(row for row in self.rows.values() if row["external_id"] == identity)
            return 200, row | {"context_cep": parameters["cep"]}
        context = {key: value for key, value in parameters.items() if key != "page"}
        return 200, {
            "context": context,
            "cards": list(self.rows.values()),
            "next": None,
            "end": True,
            "empty": False,
        }


def fail_next_condition_write(instance: FoundationInstance, delay: float = 0) -> None:
    """A test-only PostgreSQL fault fails BEFORE commit; sequence proves activation.

    Sequence advancement survives rollback, so the following real web POST can recover.
    No simulator or fault flag is installed in production composition.
    """
    with instance.database() as connection:
        connection.execute("DROP TRIGGER IF EXISTS condition_fault ON runtime_manualcondition")
        connection.execute("DROP SEQUENCE IF EXISTS condition_fault_calls")
        connection.execute("CREATE SEQUENCE condition_fault_calls")
        connection.execute(f"""
            CREATE OR REPLACE FUNCTION condition_test_fault() RETURNS trigger AS $$
            BEGIN
                IF nextval('condition_fault_calls') = 1 THEN
                    PERFORM pg_sleep({float(delay)});
                    RAISE EXCEPTION 'controlled_condition_write_failure';
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
        """)
        connection.execute("""
            CREATE TRIGGER condition_fault BEFORE INSERT OR UPDATE ON runtime_manualcondition
            FOR EACH ROW EXECUTE FUNCTION condition_test_fault()
        """)


def clear_condition_fault(instance: FoundationInstance) -> None:
    with instance.database() as connection:
        connection.execute("DROP TRIGGER IF EXISTS condition_fault ON runtime_manualcondition")
        connection.execute("DROP FUNCTION IF EXISTS condition_test_fault()")
        connection.execute("DROP SEQUENCE IF EXISTS condition_fault_calls")
