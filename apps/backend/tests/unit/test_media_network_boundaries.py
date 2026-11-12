from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from unittest.mock import patch

import pytest

from garimpei.domain.media.errors import MediaError
from garimpei.domain.media.policy import MediaPolicy
from garimpei.infra.gateway.media.image_transport import BoundedImageTransport, PinnedConnection
from tests.factories.media import CORPUS


@pytest.fixture
def faulty_media_origin() -> Iterator[tuple[str, list[dict[str, str]]]]:
    requests: list[dict[str, str]] = []

    class FaultyImageServer(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            requests.append(dict(self.headers))
            if self.path == "/redirect":
                self.send_response(302)
                self.send_header("Location", "http://127.0.0.1:1/forbidden")
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            data = b"<html>disguised</html>"
            if self.path == "/truncated":
                data = (CORPUS / "primary-large.jpg").read_bytes()[:200]
                self.send_header("Content-Length", str(len(data) + 50))
            self.end_headers()
            self.wfile.write(data)
            self.close_connection = True

        def log_message(self, format: str, *args: object) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), FaultyImageServer)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


@pytest.mark.parametrize(
    ("path", "reason"),
    [
        ("/fake-mime", "media_content_rejected"),
        ("/truncated", "media_truncated"),
        ("/redirect", "media_destination_rejected"),
    ],
)
def test_invalid_network_response_never_becomes_an_image(
    faulty_media_origin: tuple[str, list[dict[str, str]]], path: str, reason: str
) -> None:
    origin, requests = faulty_media_origin
    with pytest.raises(MediaError, match=reason):
        BoundedImageTransport(MediaPolicy(), origin).fetch(origin + path)
    assert len(requests) == 1
    assert all("Cookie" not in request and "Authorization" not in request for request in requests)


class WrongPeerSocket:
    closed = False

    def getpeername(self) -> tuple[str, int]:
        return "127.0.0.1", 443

    def close(self) -> None:
        self.closed = True


def test_validated_numeric_address_is_pinned_and_unexpected_peer_is_closed() -> None:
    channel = WrongPeerSocket()
    with patch(
        "garimpei.infra.gateway.media.image_transport.socket.create_connection",
        return_value=channel,
    ) as connect:
        with pytest.raises(MediaError, match="media_peer_rejected"):
            PinnedConnection("a.fbcdn.net", "93.184.216.34", 443, 1, False).connect()
    connect.assert_called_once_with(("93.184.216.34", 443), 1)
    assert channel.closed
