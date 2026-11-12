"""F13 loopback laboratory; scenario data never uses credentials or real WAHA."""

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from tests.factories.listing import Source
from tests.factories.runtime import FoundationInstance, prepare_instance

CASES = cast(
    dict[str, Any],
    json.loads((Path(__file__).parents[1] / "fixtures/navigation/cases.json").read_text()),
)


@dataclass
class NavigationSourceFake(Source):
    mode: str = "normal"
    related_ids: tuple[str, ...] = ("1304", "1305")
    extra_cards: dict[str, dict[str, object]] = field(default_factory=dict)
    stamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def respond(self, path: str, parameters: dict[str, str]) -> tuple[int, dict[str, object]]:
        self.calls.append((path, parameters.copy()))
        if path == "/cep":
            return 200, {
                "cep": parameters["cep"],
                "point": {
                    "latitude": -23.55052,
                    "longitude": -46.633308,
                    "city": "São Paulo",
                    "state": "SP",
                },
            }
        if self.mode == "challenge":
            return 403, {}
        if path.startswith("/detail/"):
            identity = path.removeprefix("/detail/")
            if self.mode == "slow_detail" and identity == "1301":
                self.held.set()
                self.release.wait(1.3)
            if self.mode == "detail_fail" and identity == "1301":
                return 503, {}
            return 200, self.card(identity) | {"context_cep": parameters["cep"]}
        context = {key: value for key, value in parameters.items() if key != "page"}
        if self.mode == "wrong_context":
            context["term"] = "foreign context"
        term, page = parameters["term"], parameters["page"]
        identities = (
            list(self.related_ids)
            if term in ("PS5 Pro", "PlayStation 5 Pro")
            else ["1302", "1306"]
            if "iPhone" in term
            else ["1303"]
            if page
            else ["1301", "1304"]
        )
        continuation = None if page or "iPhone" in term or "Pro" in term else "second"
        if self.mode == "repeated_cursor":
            continuation = "second"
        if self.mode == "expired_cursor" and page:
            return 410, {}
        return 200, {
            "context": context,
            "cards": [self.card(identity) for identity in identities],
            "next": continuation,
            "end": continuation is None,
            "empty": False,
        }

    def card(self, identity: str) -> dict[str, object]:
        return dict(self.extra_cards.get(identity, CASES["cards"].get(identity, {}))) | {
            "url": f"https://www.facebook.com/marketplace/item/{identity}/",
            "published_at": self.stamp,
            "pickup": True,
            "condition": "used",
            "location": {
                "latitude": -23.55052,
                "longitude": -46.633308,
                "city": "São Paulo",
                "state": "SP",
            },
        }


def prepare_navigation_instance(
    root: Path, private: Path, url: str | None = None
) -> FoundationInstance:
    instance = prepare_instance(root, private, "f13_" + uuid4().hex[:10])
    with instance.private_file.open("a") as output:
        output.write("GARIMPEI_AI_SERVICE_ENABLED=false\nGARIMPEI_ALERT_ENABLED=false\n")
        if url:
            output.write(f"GARIMPEI_LISTING_FIXTURE_URL={url}\n")
    return instance
