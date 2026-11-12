from urllib.parse import urlsplit


def https_media(value: object) -> str | None:
    if not isinstance(value, str):
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
