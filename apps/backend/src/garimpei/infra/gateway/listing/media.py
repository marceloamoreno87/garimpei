from urllib.parse import urlsplit

from garimpei.infra.gateway.listing.external_text import well_formed_text


def https_media(value: object) -> str | None:
    if not isinstance(value, str) or not well_formed_text(value):
        return None
    parsed = urlsplit(value)
    return (
        value
        if parsed.scheme == "https"
        and parsed.hostname
        and not parsed.username
        and not parsed.password
        else None
    )
