from dataclasses import replace
from uuid import uuid4

import pytest

from garimpei.domain.listing.ports import SourceFailure
from garimpei.domain.listing.scope import Scope
from garimpei.domain.monitoring.snapshot import MonitoringSnapshot
from garimpei.infra.gateway.listing.fixture_source import FixtureSource
from tests.factories.listing import CATEGORY, CEP, PRODUCT, Source, serve


def test_loopback_gateway_context_continuation_and_access_failures() -> None:
    source = Source()
    scope = Scope.from_snapshot(
        MonitoringSnapshot(
            configured=True,
            configuration_id=uuid4(),
            revision=1,
            cep=CEP,
            category_ids=(CATEGORY,),
            product_names=(PRODUCT,),
        )
    )
    assert scope is not None
    category = scope.searches[0]
    product = next(search for search in scope.searches if search.term == PRODUCT)
    with serve(source) as url:
        gateway = FixtureSource(url, 3)
        page = gateway.search(scope, category, None)
        assert page.continuation == "second"
        assert {
            x.external_id for x in gateway.search(scope, category, page.continuation).candidates
        } == {"101", "105"}
        assert gateway.detail(scope, "101").evidence.delivery_cep == CEP
        assert gateway.resolve(CEP) is not None
        source.mode = "wrong_context"
        with pytest.raises(SourceFailure, match="wrong_search_context"):
            gateway.search(scope, product, None)
        source.mode = "limited"
        with pytest.raises(SourceFailure, match="source_rate_limit") as limited:
            gateway.search(scope, product, None)
        assert limited.value.retry_after == 90 and not limited.value.access
        source.mode = "access"
        with pytest.raises(SourceFailure, match="access_denied") as blocked:
            gateway.search(scope, product, None)
        assert blocked.value.access
        source.mode = "partial"
        with pytest.raises(SourceFailure, match="source_http_503"):
            gateway.search(scope, category, page.continuation)
        with pytest.raises(SourceFailure, match="source_http_503"):
            gateway.detail(scope, "102")
        source.mode = "empty"
        empty = gateway.search(scope, replace(product, modality="shipping"), None)
        assert empty.continuation is None and not empty.candidates
