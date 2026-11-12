import json
import math
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import cast


class IntegrationError(Exception):
    code = "INTEGRATION_INVALID"
    status = 400

    def __init__(self, message: str = "Confira os dados e tente novamente.") -> None:
        super().__init__(message)
        self.message = message


class IntegrationUnavailable(IntegrationError):
    code = "INTEGRATION_UNAVAILABLE"
    status = 503

    def __init__(self) -> None:
        super().__init__("Não foi possível consultar a integração. Tente novamente em instantes.")


@dataclass(frozen=True)
class FacebookCookie:
    name: str
    value: str = field(repr=False)
    domain: str = ".facebook.com"
    path: str = "/"
    expires: float = -1
    httpOnly: bool = True
    secure: bool = True
    sameSite: str = "Lax"


@dataclass(frozen=True)
class FacebookSession:
    cookies: tuple[FacebookCookie, ...] = field(repr=False)

    @classmethod
    def parse(cls, raw: str, now: datetime) -> "FacebookSession":
        try:
            return cls._parse(raw, now)
        except (ValueError, TypeError, KeyError, OverflowError):
            raise IntegrationError(
                "Cookies inválidos. Cole o cabeçalho Cookie ou um JSON exportado do Facebook, incluindo c_user e xs válidos."
            ) from None

    @classmethod
    def _parse(cls, raw: str, now: datetime) -> "FacebookSession":
        if not raw.strip() or len(raw.encode()) > 131072:
            raise ValueError()
        value: object
        if raw.lstrip().startswith(("[", "{")):
            value = json.loads(raw)
            value = value.get("cookies") if isinstance(value, dict) else value
        else:
            header = re.sub(r"^\s*Cookie\s*:\s*", "", raw, flags=re.I)
            pairs = [part.strip().partition("=") for part in header.split(";") if part.strip()]
            value = [dict(name=name, value=val) for name, sep, val in pairs if sep]
        if not isinstance(value, list) or not value or len(value) > 100:
            raise ValueError()
        cookies = tuple(_cookie(item, now) for item in value)
        names = {item.name for item in cookies}
        if not {"c_user", "xs"} <= names or len(names) != len(cookies):
            raise ValueError()
        return cls(cookies)


def _cookie(item: object, now: datetime) -> FacebookCookie:
    if not isinstance(item, dict):
        raise ValueError()
    row = cast(dict[str, object], item)
    name, value = row.get("name"), row.get("value")
    domain = row.get("domain", ".facebook.com")
    expires = row.get("expires", row.get("expirationDate", -1))
    if (
        not isinstance(name, str)
        or not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", name)
        or not isinstance(value, str)
        or not value
        or len(value) > 16384
        or any(ord(char) < 32 for char in value)
    ):
        raise ValueError()
    if not isinstance(domain, str) or not (
        domain.lstrip(".") == "facebook.com" or domain.endswith(".facebook.com")
    ):
        raise ValueError()
    if not isinstance(expires, (int, float)) or not math.isfinite(expires):
        raise ValueError()
    if row.get("session") is True:
        expires = -1
    if expires >= 0:
        datetime.fromtimestamp(expires, UTC)
    if name in {"c_user", "xs"} and expires >= 0 and expires <= now.timestamp():
        raise ValueError()
    if name == "c_user" and not value.isdecimal():
        raise ValueError()
    same_site = str(row.get("sameSite", "Lax")).capitalize()
    if same_site not in {"Strict", "Lax", "None"}:
        same_site = "Lax"
    return FacebookCookie(
        name, value, domain, "/", float(expires), bool(row.get("httpOnly", True)), True, same_site
    )


@dataclass(frozen=True)
class Group:
    id: str
    name: str


def group_id(value: str) -> bool:
    return re.fullmatch(r"[0-9]+(?:-[0-9]+)?@g\.us", value) is not None


@dataclass(frozen=True)
class ConnectionState:
    phase: str = "STOPPED"
    account: str = field(default="", repr=False)


@dataclass(frozen=True)
class IntegrationConfiguration:
    facebook_revision: int = 0
    facebook_saved_at: datetime | None = None
    facebook_expires_at: datetime | None = None
    facebook_phase: str = "missing"
    whatsapp_configured: bool = False
    whatsapp_session: str = ""
    whatsapp_account: str = field(default="", repr=False)
    whatsapp_group: str = ""
    whatsapp_group_name: str = ""
    alerts_enabled: bool = False
    facebook_mode: str = "cookies"
    facebook_login_state: str = ""


@dataclass(frozen=True)
class IntegrationView:
    configuration: IntegrationConfiguration
    whatsapp: ConnectionState
    groups: tuple[Group, ...] = ()
    groups_unavailable: bool = False
