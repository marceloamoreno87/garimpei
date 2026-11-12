from dataclasses import replace
from unittest.mock import Mock
from uuid import uuid4

from garimpei.domain.listing.listing import Candidate, Evidence, Match
from garimpei.domain.listing.ports import Attempt, Page, Revisit, Work
from garimpei.domain.listing.scope import Scope, Search
from garimpei.domain.navigation.catalog import Catalog
from garimpei.domain.navigation.policy import NavigationPolicy
from garimpei.domain.navigation.work import NavigationUnit, Turn
from garimpei.usecase.navigation.run_slice_usecase import RunSliceUseCase


def test_first_page_limit_ends_entire_slice_before_details() -> None:
    query = Search(Match("product", "ps5 slim"), "PS5 Slim", "marketplace")
    scope = Scope(uuid4(), "facebook_marketplace", "01001000", 4, "key", (query,))
    unit = NavigationUnit(
        Turn(uuid4(), query.key, "discovery", 0, None),
        1,
        4,
        query,
        ("PS5 Slim",),
        0,
        None,
        (),
        0,
        0,
        0,
        None,
        "page",
    )
    detail = replace(
        unit,
        turn=replace(unit.turn, front="investigation"),
        target=Revisit("1301", (query.interest,)),
        unit_key="detail:1301",
    )
    collection = Mock()
    collection.begin.return_value = Work(scope, frozenset(), False)
    navigation = Mock()
    navigation.claim.side_effect = [unit, detail, None]
    source = Mock()
    source.search.return_value = Page((), None)
    source.detail.return_value = Candidate("1301", Evidence(title="PS5 Slim"), "detail")
    geocoding = Mock()
    geocoding.resolve.return_value = None
    policy = replace(NavigationPolicy(), slice_pages=1)
    RunSliceUseCase(
        collection,
        navigation,
        source,
        geocoding,
        Catalog("1", (), ()),
        policy,
        lambda: 0.0,
        20,
        1.2,
    ).execute(Attempt(uuid4(), 1))
    assert source.search.call_count == 1
    assert source.detail.call_count == 0
