from dataclasses import replace
from unittest.mock import Mock
from uuid import uuid4

from garimpei.domain.listing.listing import Candidate, Evidence, Match
from garimpei.domain.listing.ports import Attempt, Page, Revisit, Work
from garimpei.domain.listing.scope import Scope, Search
from garimpei.domain.navigation.catalog import Catalog
from garimpei.domain.navigation.policy import NavigationPolicy
from garimpei.domain.navigation.work import NavigationUnit, Turn
from garimpei.domain.robot.errors import RobotPaused
from garimpei.usecase.navigation.run_slice_usecase import RunSliceUseCase
from tests.factories.robot import RobotAdmissionFake


def test_pause_after_authorized_page_keeps_checkpoint_and_denies_next_detail() -> None:
    query = Search(Match("product", "ps5 slim"), "PS5 Slim", "marketplace")
    scope = Scope(uuid4(), "facebook_marketplace", "01001000", 4, "key", (query,))
    page = NavigationUnit(
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
    detail = replace(page, target=Revisit("1301", (query.interest,)), unit_key="detail:1301")
    collection, navigation, source, geocoding = Mock(), Mock(), Mock(), Mock()
    collection.begin.return_value = Work(scope, frozenset(), False)
    navigation.claim.side_effect = [page, detail, None]
    robot = RobotAdmissionFake()

    def response(*_args: object) -> Page:
        robot.enabled = False
        return Page((), None)

    source.search.side_effect = response
    source.detail.return_value = Candidate("1301", Evidence(title="PS5 Slim"), "detail")
    RunSliceUseCase(
        collection,
        navigation,
        source,
        geocoding,
        Catalog("1", (), ()),
        NavigationPolicy(),
        lambda: 0.0,
        20,
        1.2,
        robot=robot,
    ).execute(Attempt(uuid4(), 1))
    assert source.search.call_count == navigation.page.call_count == 1
    assert (
        source.detail.call_count
        == navigation.detail.call_count
        == navigation.failed.call_count
        == 0
    )
    assert navigation.yield_slice.call_count == 1
    assert robot.outcomes == [("navigation_context", "completed"), ("navigation", "completed")]


def test_pause_after_preparation_is_not_authorization_and_does_not_invoke_geocoding() -> None:
    query = Search(Match("product", "ps5 slim"), "PS5 Slim", "marketplace")
    scope = Scope(uuid4(), "facebook_marketplace", "01001000", 4, "key", (query,))
    collection, navigation, source, geocoding = Mock(), Mock(), Mock(), Mock()
    collection.begin.return_value = Work(scope, frozenset(), False)
    robot = RobotAdmissionFake()
    navigation.prepare.side_effect = lambda *_args: setattr(robot, "enabled", False)
    RunSliceUseCase(
        collection,
        navigation,
        source,
        geocoding,
        Catalog("1", (), ()),
        NavigationPolicy(),
        lambda: 0.0,
        20,
        1.2,
        robot=robot,
    ).execute(Attempt(uuid4(), 1))
    geocoding.resolve.assert_not_called()
    source.search.assert_not_called()
    navigation.failed.assert_not_called()
    navigation.yield_slice.assert_called_once()


def test_media_denial_releases_prepared_claim_without_fetch_or_failure() -> None:
    from garimpei.usecase.media.obtain_media_usecase import ObtainMediaUseCase

    repository, transport, store, clock, on_pause = Mock(), Mock(), Mock(), Mock(), Mock()
    claim = Mock(kind="download", variants=(Mock(url="https://example.invalid/photo"),))
    repository.claim.return_value = claim
    ObtainMediaUseCase(
        repository, transport, store, clock, RobotAdmissionFake(False), on_pause
    ).execute(uuid4())
    transport.fetch.assert_not_called()
    repository.publish.assert_not_called()
    repository.fail.assert_not_called()
    on_pause.assert_called_once_with(claim)


def test_valuation_denial_is_control_flow_not_failed_work() -> None:
    from garimpei.infra.worker.valuation_handler import ValuationTaskHandler

    identity = uuid4()
    evaluate, store, clock, paused = Mock(), Mock(), Mock(), Mock()
    evaluate.execute.side_effect = RobotPaused()
    ValuationTaskHandler(evaluate, store, clock, paused).execute(identity)
    store.failed.assert_not_called()
    paused.assert_called_once_with(identity)
