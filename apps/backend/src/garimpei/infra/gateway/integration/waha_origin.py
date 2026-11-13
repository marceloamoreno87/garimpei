"""Admit loopback fixtures or the explicitly approved private Compose service."""

from urllib.parse import urlsplit


def waha_origin(url: str, internal_service: bool = False) -> tuple[str, int]:
    parsed = urlsplit(url)
    host, port = parsed.hostname, parsed.port
    local = host == "127.0.0.1" and port is not None
    private = internal_service and host == "waha" and port == 3000
    if (
        parsed.scheme != "http"
        or not (local or private)
        or parsed.username
        or parsed.password
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("WAHA requires loopback HTTP or the approved private Compose origin")
    assert host is not None and port is not None
    return host, port
