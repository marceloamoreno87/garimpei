"""A JSON blob does not grant permission to archive credentials or private access URLs."""

from urllib.parse import parse_qsl, urlsplit

from garimpei.infra.gateway.operations.archive_gateway import ArchiveInvalid

FORBIDDEN = frozenset(
    {
        "cookie",
        "cookies",
        "authorization",
        "access_token",
        "refresh_token",
        "password",
        "secret",
        "api_key",
        "storage_state",
        "storageState",
        "headers",
        "qr",
        "qrcode",
    }
)
SIGNED_QUERY = frozenset(
    {
        "token",
        "access_token",
        "auth",
        "authorization",
        "signature",
        "sig",
        "key",
        "api_key",
        "password",
        "secret",
        "x-amz-signature",
        "x-amz-credential",
        "oh",
    }
)


def validate_private_fields(value: object) -> None:
    if isinstance(value, dict):
        _validate_mapping(value)
        return
    if isinstance(value, list):
        for child in value:
            validate_private_fields(child)
        return
    if isinstance(value, str) and value.startswith(("http://", "https://")):
        _validate_url(value)


def _validate_mapping(value: dict[object, object]) -> None:
    for key, child in value.items():
        if str(key).casefold() in {name.casefold() for name in FORBIDDEN}:
            raise ArchiveInvalid("archive_credential_field")
        validate_private_fields(child)


def _validate_url(value: str) -> None:
    parsed = urlsplit(value)
    if parsed.username or parsed.password or not parsed.hostname:
        raise ArchiveInvalid("archive_private_url")
    if any(key.casefold() in SIGNED_QUERY for key, _ in parse_qsl(parsed.query)):
        raise ArchiveInvalid("archive_private_url")


def sanitize_transient_media(value: object, field: str = "", media_context: bool = False) -> object:
    """Preserve media identity while excluding its temporary access query by schema."""
    if isinstance(value, dict):
        return {
            str(key): sanitize_transient_media(
                child,
                str(key),
                media_context or field in {"media", "photos", "variants", "candidates"},
            )
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [
            sanitize_transient_media(
                child,
                field,
                media_context or field in {"media", "photos", "variants", "candidates"},
            )
            for child in value
        ]
    if isinstance(value, str) and (
        field in {"image_url", "photo_url", "source_url"} or (field == "url" and media_context)
    ):
        return _public_media_origin(value)
    return value


def _public_media_origin(value: str) -> str:
    parsed = urlsplit(value)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        raise ArchiveInvalid("archive_private_media_url")
    return parsed._replace(query="", fragment="").geturl()
