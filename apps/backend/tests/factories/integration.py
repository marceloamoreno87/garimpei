import base64
import json
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import parse_qs, unquote, urlsplit

from tests.factories.listing import ControlledClock, Source, prepare_listing_instance, serve
from tests.factories.runtime import FoundationInstance
from tests.integration.test_collection import command

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a7WQAAAAASUVORK5CYII="
)


@dataclass
class SessionServer:
    present: bool = False
    phase: str = "STOPPED"
    account: str = "200@c.us"
    unavailable: bool = False
    groups: list[dict[str, object]] = field(
        default_factory=lambda: [
            {"JID": "12345@g.us", "Name": "Garimpo de teste"},
            {"id": "54321-123@g.us", "subject": "Outro grupo"},
        ]
    )
    calls: list[tuple[str, str]] = field(default_factory=list)
    messages: list[dict[str, object]] = field(default_factory=list)
    receipt_shape: str = "normalized"


@contextmanager
def serve_session(state: SessionServer) -> Iterator[str]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            state.calls.append(("GET", self.path))
            if state.unavailable:
                self.respond(503, {})
                return
            path = urlsplit(self.path)
            if path.path.startswith("/api/sessions/"):
                self.respond(
                    200 if state.present else 404,
                    {"status": state.phase, "me": {"id": state.account}},
                )
                return
            if "/groups" in path.path:
                parameters = parse_qs(path.query)
                offset = int(parameters.get("offset", ["0"])[0])
                limit = int(parameters.get("limit", ["100"])[0])
                self.respond(200, state.groups[offset : offset + limit])
                return
            if "/auth/qr" in path.path:
                self.respond(200, PNG)
                return
            if "/messages/" in path.path:
                identity = unquote(path.path.split("/messages/")[1])
                value = next((item for item in state.messages if item["id"] == identity), None)
                self.respond(200 if value else 404, value or {})
                return
            parameters = parse_qs(path.query)
            offset = int(parameters.get("offset", ["0"])[0])
            limit = int(parameters.get("limit", ["100"])[0])
            self.respond(200, state.messages[offset : offset + limit])

        def do_POST(self) -> None:
            state.calls.append(("POST", self.path))
            body = json.loads(
                self.rfile.read(int(self.headers.get("Content-Length", "0"))) or b"{}"
            )
            if self.path == "/api/sendText":
                message = {
                    "id": f"group-message-{len(state.messages)}",
                    "body": body["text"],
                    "fromMe": True,
                    "from": body["chatId"],
                    "to": state.account,
                    "participant": state.account,
                    "ack": 1,
                }
                if state.receipt_shape == "gows_lid":
                    message.update(
                        {
                            "to": None,
                            "participant": None,
                            "_data": {
                                "Info": {
                                    "Chat": body["chatId"],
                                    "Sender": "220@lid",
                                    "SenderAlt": state.account.replace("@c.us", "@s.whatsapp.net"),
                                    "IsFromMe": True,
                                    "IsGroup": body["chatId"].endswith("@g.us"),
                                }
                            },
                        }
                    )
                state.messages.append(message)
                self.respond(200, message)
                return
            state.present, state.phase = True, "SCAN_QR_CODE"
            self.respond(201 if self.path == "/api/sessions" else 200, {})

        def respond(self, status: int, data: object) -> None:
            raw = data if isinstance(data, bytes) else json.dumps(data).encode()
            self.send_response(status)
            self.send_header(
                "Content-Type", "image/png" if isinstance(data, bytes) else "application/json"
            )
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def log_message(self, _format: str, *args: object) -> None:
            pass

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}"
        finally:
            server.shutdown()
            thread.join()


type IntegrationScenario = tuple[FoundationInstance, Source, ControlledClock, SessionServer, Path]


@contextmanager
def integration_scenario(private: Path) -> Iterator[IntegrationScenario]:
    source, state = Source(), SessionServer()
    with serve(source) as url, serve_session(state) as waha:
        instance, clock = prepare_listing_instance(
            Path(__file__).resolve().parents[4], private, url
        )
        credentials = private / "private-session"
        with instance.private_file.open("a") as output:
            output.write(
                f"GARIMPEI_ALERT_FIXTURE_URL={waha}\nGARIMPEI_INTEGRATION_PRIVATE_DIR={credentials}\n"
            )
        command(instance, "./scripts/init.sh", "--disposable")
        try:
            yield instance, source, clock, state, credentials
        finally:
            command(instance, "./scripts/stop.sh", "--clean")
