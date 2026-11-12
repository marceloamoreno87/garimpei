import json
import socket
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Event, Thread
from typing import cast
from urllib.parse import parse_qs, unquote, urlsplit

from garimpei.domain.alert.alert import Binding, Delivery, Outcome


@dataclass
class WahaServer:
    ready: bool = True
    authenticated: bool = True
    mode: str = "confirmed"
    ack: int = 1
    account: str = "200@c.us"
    calls: list[tuple[str, str]] = field(default_factory=list)
    messages: list[dict[str, object]] = field(default_factory=list)
    held: Event = field(default_factory=Event)
    release: Event = field(default_factory=Event)
    hold_post: bool = False


@contextmanager
def serve_waha(state: WahaServer) -> Iterator[str]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            state.calls.append(("GET", self.path))
            url = urlsplit(self.path)
            if "/api/sessions/" in url.path:
                self.respond(
                    200 if state.authenticated else 401,
                    {
                        "status": "WORKING" if state.ready else "SCAN_QR_CODE",
                        "me": {"id": state.account},
                    },
                )
                return
            if "/messages/" in url.path:
                identity = unquote(url.path.split("/messages/")[1])
                value = next((x for x in state.messages if x["id"] == identity), None)
                self.respond(200 if value else 404, value or {})
                return
            offset = int(parse_qs(url.query).get("offset", ["0"])[0])
            limit = int(parse_qs(url.query).get("limit", ["100"])[0])
            self.respond(200, state.messages[offset : offset + limit])

        def do_POST(self) -> None:
            state.calls.append(("POST", self.path))
            body = cast(
                dict[str, object], json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            )
            assert body["session"] == "synthetic" and body["chatId"] == "100@c.us"
            assert body["linkPreview"] is False
            message = {
                "id": f"message-{len(state.messages) + 1}",
                "fromMe": True,
                "to": body["chatId"],
                "from": state.account,
                "body": body["text"],
                "ack": state.ack,
            }
            if state.mode != "lost_empty":
                state.messages.append(message)
            if state.hold_post:
                state.held.set()
                state.release.wait(15)
            if state.mode in {"lost", "lost_empty"}:
                self.connection.shutdown(socket.SHUT_RDWR)
                self.connection.close()
                return
            self.respond(200, {} if state.mode == "incomplete" else message)

        def respond(self, status: int, body: object) -> None:
            data = json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
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
            state.release.set()
            server.shutdown()
            thread.join()


class UnavailableSessionGateway:
    def check(self, _binding: "Binding") -> bool:
        return False

    def send(self, _delivery: "Delivery") -> "Outcome":
        raise AssertionError("An unavailable session must not send")

    def reconcile(self, _delivery: "Delivery", _now: "datetime") -> "Outcome":
        raise AssertionError("An unavailable session must not query messages")
