"""Credential-free HTTP transport: DNS pinning, peer verification and bounded decoding."""

import hashlib
import http.client
import ipaddress
import socket
import ssl
import time
import warnings
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from io import BytesIO
from threading import Event, Thread
from urllib.parse import SplitResult, urljoin, urlsplit

from PIL import Image, UnidentifiedImageError

from garimpei.domain.media.errors import MediaError
from garimpei.domain.media.media import Transfer
from garimpei.domain.media.policy import MediaPolicy


class PinnedConnection(http.client.HTTPSConnection):
    def __init__(self, host: str, address: str, port: int, timeout: float, secure: bool) -> None:
        super().__init__(host, port, timeout=timeout, context=ssl.create_default_context())
        self._address, self._secure = address, secure
        self._tls_context = ssl.create_default_context()

    def connect(self) -> None:
        channel = socket.create_connection((self._address, self.port), self.timeout)
        if channel.getpeername()[0] != self._address:
            channel.close()
            raise MediaError("media_peer_rejected")
        self.sock = (
            self._tls_context.wrap_socket(channel, server_hostname=self.host)
            if self._secure
            else channel
        )


class BoundedImageTransport:
    def __init__(self, policy: MediaPolicy, eval_origin: str | None = None) -> None:
        self._policy, self._eval_origin = policy, eval_origin

    def fetch(self, url: str) -> Transfer:
        deadline = time.monotonic() + self._policy.timeout_seconds
        for _ in range(4):
            parsed, addresses = self._target(url, deadline)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise MediaError("media_transfer_timeout")
            result = self._request(parsed, addresses[0], remaining, deadline)
            if isinstance(result, str):
                url = result
                continue
            return result
        raise MediaError("media_redirect_limit")

    def _request(
        self, parsed: "SplitResult", address: str, remaining: float, deadline: float
    ) -> Transfer | str:
        connection = PinnedConnection(
            parsed.hostname or "",
            address,
            parsed.port or 443,
            min(5, remaining),
            parsed.scheme == "https",
        )
        try:
            connection.request(
                "GET",
                parsed.path + ("?" + parsed.query if parsed.query else ""),
                headers={
                    "Accept-Encoding": "identity",
                    "Accept": "image/jpeg,image/png,image/webp",
                },
            )
            response = connection.getresponse()
            if response.status in {301, 302, 303, 307, 308}:
                return urljoin(parsed.geturl(), response.getheader("Location", ""))
            return self._receive(response, connection, deadline)
        except (OSError, http.client.HTTPException):
            raise MediaError("media_transfer_failed") from None
        finally:
            connection.close()

    def _target(self, url: str, deadline: float) -> tuple[SplitResult, list[str]]:
        try:
            parsed = urlsplit(url)
            host, port = parsed.hostname or "", parsed.port
        except ValueError:
            raise MediaError("media_destination_rejected") from None
        if len(url) > 8192 or parsed.username or parsed.password or parsed.fragment:
            raise MediaError("media_destination_rejected")
        evaluation = (
            self._eval_origin is not None
            and f"{parsed.scheme}://{parsed.netloc}" == self._eval_origin
        )
        allowed = any(
            host == suffix or host.endswith("." + suffix) for suffix in ("fbcdn.net", "fbsbx.com")
        )
        if not evaluation and (parsed.scheme != "https" or port not in {None, 443} or not allowed):
            raise MediaError("media_destination_rejected")
        addresses = resolve_addresses(host, port or 443, deadline)
        if not addresses or (
            not evaluation and any(not ipaddress.ip_address(a).is_global for a in addresses)
        ):
            raise MediaError("media_destination_rejected")
        # The connected socket uses the validated numeric address, never a second DNS lookup.
        return parsed, addresses

    def _receive(
        self, response: http.client.HTTPResponse, connection: PinnedConnection, deadline: float
    ) -> Transfer:
        if response.status != 200:
            delay = response.getheader("Retry-After", "0")
            raise MediaError(
                "media_source_expired"
                if response.status in {403, 404, 410}
                else "media_source_failed",
                retry_after=source_delay(delay),
            )
        if response.getheader("Content-Encoding", "identity") != "identity":
            raise MediaError("media_encoding_rejected")
        length = response.getheader("Content-Length")
        if length and (not length.isdecimal() or int(length) > self._policy.max_file_bytes):
            raise MediaError("media_file_limit")
        chunks: list[bytes] = []
        size = 0
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise MediaError("media_transfer_timeout")
            if connection.sock:
                connection.sock.settimeout(min(5, remaining))
            chunk = response.read1(min(65536, self._policy.max_file_bytes + 1 - size))
            size += len(chunk)
            if size > self._policy.max_file_bytes:
                raise MediaError("media_file_limit")
            if not chunk:
                break
            chunks.append(chunk)
        if length and size != int(length):
            raise MediaError("media_truncated")
        return validate_image(
            b"".join(chunks),
            response.getheader("Content-Type", "").split(";")[0].strip(),
            self._policy,
        )


def validate_image(data: bytes, mime: str, policy: MediaPolicy) -> Transfer:
    if len(data) > policy.max_file_bytes:
        raise MediaError("media_file_limit")
    try:
        width, height = inspect_image(data, mime, policy)
    except (
        OSError,
        ValueError,
        UnidentifiedImageError,
        Image.DecompressionBombWarning,
        Image.DecompressionBombError,
    ):
        raise MediaError("media_content_rejected") from None
    return Transfer(data, mime, width, height, hashlib.sha256(data).hexdigest())


def source_delay(value: str) -> int:
    if value.isdecimal():
        return int(value)
    try:
        return max(0, int((parsedate_to_datetime(value) - datetime.now(UTC)).total_seconds()) + 1)
    except (ValueError, TypeError, OverflowError):
        return 0


def resolve_addresses(host: str, port: int, deadline: float) -> list[str]:
    done = Event()
    result: list[str] = []

    def resolve() -> None:
        try:
            result.extend(
                str(row[4][0]) for row in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
            )
        except OSError:
            pass
        finally:
            done.set()

    Thread(target=resolve, daemon=True).start()
    if not done.wait(max(0, deadline - time.monotonic())):
        raise MediaError("media_transfer_timeout")
    if not result:
        raise MediaError("media_dns_failed")
    return list(dict.fromkeys(result))


def inspect_image(data: bytes, mime: str, policy: MediaPolicy) -> tuple[int, int]:
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        return decode_image(data, mime, policy)


def decode_image(data: bytes, mime: str, policy: MediaPolicy) -> tuple[int, int]:
    with Image.open(BytesIO(data), formats=("JPEG", "PNG", "WEBP")) as image:
        actual = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}.get(
            image.format or ""
        )
        width, height = image.size
        if width <= 0 or height <= 0 or width * height > policy.max_pixels:
            raise MediaError("media_pixel_limit")
        if actual != mime or getattr(image, "n_frames", 1) != 1:
            raise MediaError("media_content_rejected")
        image.verify()
    with Image.open(BytesIO(data)) as decoded:
        decoded.load()
    return width, height
