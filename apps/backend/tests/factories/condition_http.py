import re
from dataclasses import dataclass, field
from http.cookiejar import CookieJar
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import (
    HTTPCookieProcessor,
    HTTPRedirectHandler,
    OpenerDirector,
    Request,
    build_opener,
)

from tests.factories.runtime import FoundationInstance


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(
        self, req: Request, fp: object, code: int, msg: str, headers: object, newurl: str
    ) -> None:
        return None


@dataclass
class ConditionBrowser:
    instance: FoundationInstance
    opener: OpenerDirector = field(init=False)

    def __post_init__(self) -> None:
        self.opener = build_opener(HTTPCookieProcessor(CookieJar()), NoRedirect())

    def request(
        self, path: str, data: dict[str, str] | None = None, method: str | None = None
    ) -> tuple[int, str, str]:
        request = Request(
            f"http://127.0.0.1:{self.instance.config.web_port}{path}",
            data=urlencode(data).encode() if data is not None else None,
            method=method,
        )
        try:
            with self.opener.open(request, timeout=15) as response:
                return (
                    response.status,
                    response.read().decode(),
                    response.headers.get("Location", ""),
                )
        except HTTPError as error:
            return error.code, error.read().decode(), error.headers.get("Location", "")

    def choose(
        self, identity: str, choice: str, revision: str | None = None
    ) -> tuple[int, str, str]:
        status, body, _ = self.request(f"/ofertas/{identity}/")
        assert status == 200
        token = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', body)
        current = re.search(r'name="revision" value="([^"]+)"', body)
        assert token is not None and current is not None
        return self.request(
            f"/ofertas/{identity}/condicao/",
            {
                "choice": choice,
                "revision": revision if revision is not None else current[1],
                "csrfmiddlewaretoken": token[1],
            },
        )


def listing_id(instance: FoundationInstance, external: str = "506") -> str:
    with instance.database() as connection:
        row = connection.execute(
            "SELECT id FROM runtime_listing WHERE external_id=%s", [external]
        ).fetchone()
        assert row is not None
        return str(row[0])
