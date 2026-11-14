import json
from http.client import HTTPConnection, HTTPException
from urllib.parse import quote, urlencode

from garimpei.domain.integration.values import (
    ConnectionState,
    Group,
    IntegrationUnavailable,
    group_id,
)
from garimpei.infra.gateway.integration.waha_origin import waha_origin


class WahaSessionGateway:
    def __init__(self, url: str, key: str, timeout: int, *, internal_service: bool = False) -> None:
        self._host, self._port = waha_origin(url, internal_service)
        self._key, self._timeout = key, timeout

    def _raw(
        self,
        method: str,
        path: str,
        body: dict[str, object] | None = None,
        *,
        accept: str = "application/json",
    ) -> tuple[int, bytes]:
        connection = HTTPConnection(self._host, self._port, timeout=self._timeout)
        try:
            connection.request(
                method,
                path,
                json.dumps(body).encode() if body is not None else None,
                {"X-Api-Key": self._key, "Accept": accept, "Content-Type": "application/json"},
            )
            response = connection.getresponse()
            data = response.read(2_000_001)
            if len(data) > 2_000_000:
                raise ValueError()
            return response.status, data
        except (OSError, HTTPException, ValueError):
            raise IntegrationUnavailable() from None
        finally:
            connection.close()

    def _json(
        self, method: str, path: str, body: dict[str, object] | None = None
    ) -> tuple[int, object]:
        status, data = self._raw(method, path, body)
        try:
            return status, json.loads(data) if data else None
        except ValueError:
            raise IntegrationUnavailable() from None

    def state(self, session: str) -> ConnectionState:
        try:
            status, data = self._json("GET", "/api/sessions/" + quote(session, safe=""))
            if status == 404:
                return ConnectionState()
            if status != 200 or not isinstance(data, dict):
                return ConnectionState("UNAVAILABLE")
            phase = str(data.get("status", "UNAVAILABLE"))
            me = data.get("me")
            account = str(me.get("id") or "") if isinstance(me, dict) else ""
            if phase == "WORKING" and not account:
                return ConnectionState("UNAVAILABLE")
            return ConnectionState(phase, account)
        except IntegrationUnavailable:
            return ConnectionState("UNAVAILABLE")

    def connect(self, session: str) -> None:
        path = "/api/sessions/" + quote(session, safe="")
        status, _ = self._json("GET", path)
        if status == 404:
            code, _ = self._json("POST", "/api/sessions", {"name": session, "start": True})
        elif status == 200:
            code, _ = self._json("POST", path + "/start")
        else:
            raise IntegrationUnavailable()
        if code not in (200, 201, 202):
            raise IntegrationUnavailable()

    def qr(self, session: str) -> bytes:
        status, data = self._raw(
            "GET", "/api/" + quote(session, safe="") + "/auth/qr?format=image", accept="image/png"
        )
        if status != 200 or not data.startswith(b"\x89PNG\r\n\x1a\n"):
            raise IntegrationUnavailable()
        return data

    def groups(self, session: str) -> tuple[Group, ...]:
        results: dict[str, Group] = {}
        for page in range(10):
            status, data = self._json(
                "GET",
                "/api/"
                + quote(session, safe="")
                + "/groups?"
                + urlencode(
                    {
                        "limit": 100,
                        "offset": 100 * page,
                        "sortBy": "id",
                        "sortOrder": "asc",
                        "exclude": "participants",
                    }
                ),
            )
            if status != 200 or not isinstance(data, list):
                raise IntegrationUnavailable()
            for item in data:
                self._group(item, results)
            if len(data) < 100:
                return tuple(sorted(results.values(), key=lambda x: (x.name.casefold(), x.id)))
        raise IntegrationUnavailable()

    @staticmethod
    def _group(value: object, results: dict[str, Group]) -> None:
        if not isinstance(value, dict):
            return
        identity = value.get("id", value.get("JID"))
        name = value.get("subject", value.get("name", value.get("Name")))
        if isinstance(identity, str) and group_id(identity) and isinstance(name, str):
            results[identity] = Group(identity, name[:300] or "Grupo sem nome")
