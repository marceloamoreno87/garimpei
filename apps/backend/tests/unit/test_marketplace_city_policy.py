import hashlib
import json
from uuid import uuid4

from garimpei.domain.listing.geography import Point
from garimpei.domain.listing.listing import Match
from garimpei.domain.listing.scope import Scope, Search
from garimpei.domain.monitoring.snapshot import MonitoringSnapshot
from garimpei.domain.monitoring.values import CategoryCatalog
from garimpei.infra.gateway.listing.facebook_marketplace import FacebookMarketplace
from garimpei.infra.gateway.listing.relay_parser import Feed
from tests.unit.test_marketplace_source import RecordedNavigation


def test_native_city_origin_is_independent_of_the_registered_postal_code() -> None:
    from urllib.parse import parse_qs, urlsplit

    city = Point(-23.55, -46.6333, None, "São Paulo", "SP")
    browser = RecordedNavigation((Feed((), False, True),), [])
    source = FacebookMarketplace(browser, city, CategoryCatalog("", "", ()))
    for cep in ("01001000", "22222222", "04132001"):
        scope = Scope(uuid4(), "facebook_marketplace", cep, 1, cep, ())
        query = Search(
            Match("product", "playstation 5"), "PlayStation 5", "marketplace", purpose="research"
        )
        result = source.search(scope, query, None)
        assert result.source_context is not None and result.source_context.verified
        params = parse_qs(urlsplit(browser.calls[-1]).query)
        assert params["latitude"] == ["-23.55"]
        assert params["longitude"] == ["-46.6333"]
        assert params["radius"] == ["20"]
        assert "/marketplace/saopaulo/search/" in browser.calls[-1]
        assert cep not in browser.calls[-1]


def test_city_policy_supersedes_the_previous_postal_search_signature() -> None:
    config = MonitoringSnapshot(
        configured=True,
        configuration_id=uuid4(),
        source="facebook_marketplace",
        revision=1,
        cep="01001000",
        product_names=("RTX 4060 8GB",),
    )
    scope = Scope.from_snapshot(config)
    assert scope is not None
    old = hashlib.sha256(
        json.dumps(
            [
                "facebook_marketplace",
                "01001000",
                [("product", "rtx 4060 8gb")],
                "48h-marketplace-potential-v4",
                20,
            ]
        ).encode()
    ).hexdigest()
    assert scope.key != old
