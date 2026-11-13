import asyncio
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import cast
from uuid import uuid4

import pytest
from playwright.sync_api import Page, Response

from garimpei.domain.listing.geography import Point
from garimpei.domain.robot.control import OperationOutcome, RobotPermit
from garimpei.domain.robot.errors import RobotPaused
from garimpei.infra.gateway.listing.marketplace_browser import MarketplaceBrowser, SearchFilters
from garimpei.infra.gateway.listing.relay_parser import JsonObject
from garimpei.infra.gateway.robot.admission import robot_operation
from garimpei.infra.gateway.valuation.new_source import RetailNewSource


@dataclass
class PausingAdmission:
    enabled: bool = True
    permits: list[RobotPermit] = field(default_factory=list)
    outcomes: list[OperationOutcome] = field(default_factory=list)

    def authorize(
        self, stage: str, unit_key: str, input_revision: str, resource_generation: int
    ) -> RobotPermit | None:
        if not self.enabled:
            return None
        permit = RobotPermit(uuid4(), stage, unit_key, input_revision, resource_generation, 0)
        self.permits.append(permit)
        return permit

    def complete(
        self, permit: RobotPermit, outcome: OperationOutcome = "completed", reason: str = ""
    ) -> None:
        assert permit in self.permits
        self.outcomes.append(outcome)


class ProgrammedPage:
    def __init__(self, admission: PausingAdmission, rows: list[JsonObject]) -> None:
        self.admission, self.rows = admission, rows
        self.calls: list[str] = []
        self.url = "https://www.facebook.com/marketplace/search/"
        self.pause_after_page = True

    def goto(self, url: str, **kwargs: object) -> Response:
        self.calls.append(url)
        self.url = url
        if self.pause_after_page:
            self.admission.enabled = False
        return cast(Response, ProgrammedResponse())

    def wait_for_timeout(self, delay: int) -> None:
        pass

    def locator(self, selector: str) -> "ProgrammedPage":
        return self

    def all_text_contents(self) -> list[str]:
        return [json.dumps(self.rows)]

    def evaluate(self, expression: str, arg: object = None) -> object:
        self.calls.append("graphql" if arg is not None else "extract")
        return {
            "id": "retail-1",
            "title": "PlayStation 5 Slim 1 TB com leitor",
            "available": True,
            "prices": {"priceWithDiscount": "3000"},
            "currency": "BRL",
            "stock": "https://schema.org/InStock",
        }


class ProgrammedResponse:
    status = 200
    ok = True


def browser_with_page(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    admission: PausingAdmission,
    rows: list[JsonObject] | None = None,
) -> tuple[MarketplaceBrowser, ProgrammedPage]:
    page = ProgrammedPage(admission, rows or [])
    browser = MarketplaceBrowser(tmp_path / "session.json", 10, 0, robot=admission)
    monkeypatch.setattr(browser, "_open", lambda: cast(Page, page))
    monkeypatch.setattr(browser, "_check_access", lambda _page: None)
    return browser, page


def test_completed_page_is_retained_but_next_navigation_is_denied(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    admission = PausingAdmission()
    browser, page = browser_with_page(tmp_path, monkeypatch, admission, [{"verified": True}])
    try:
        rows, _ = browser.navigate("https://www.facebook.com/marketplace/search/?query=PS5")
        assert any(row.get("verified") is True for row in rows)
        with pytest.raises(RobotPaused):
            browser.navigate("https://www.facebook.com/marketplace/item/101/")
        assert len(page.calls) == 1
        assert admission.outcomes == ["completed"]
    finally:
        browser.close()


def test_native_search_cannot_start_graphql_fallback_after_pause(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    admission = PausingAdmission()
    template: JsonObject = {
        "queryName": "CometMarketplaceSearchContentContainerQuery",
        "queryID": "test-query",
        "variables": {"params": {"browse_request_params": {}}},
    }
    browser, page = browser_with_page(tmp_path, monkeypatch, admission, [template])
    try:
        with pytest.raises(RobotPaused):
            browser.search(
                "https://www.facebook.com/marketplace/search/?query=PS5",
                SearchFilters(Point(-23.55, -46.63, 0, "São Paulo", "SP"), 20, None),
            )
        assert len(page.calls) == 1
        assert admission.outcomes == ["completed"]
    finally:
        browser.close()


def test_retail_does_not_open_second_page_after_first_authorized_page_completes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    admission = PausingAdmission()
    page = ProgrammedPage(admission, [])
    source = RetailNewSource(tmp_path / "catalog.json", None, robot=admission)
    with pytest.raises(RobotPaused):
        source._read_pages(
            cast(Page, page),
            ("https://store.test/one", "https://store.test/two"),
            datetime(2026, 11, 13, tzinfo=UTC),
        )
    assert page.calls == ["https://store.test/one", "extract"]
    assert admission.outcomes == ["completed"]


class AsyncCheckingAdmission(PausingAdmission):
    def authorize(
        self, stage: str, unit_key: str, input_revision: str, resource_generation: int
    ) -> RobotPermit | None:
        with pytest.raises(RuntimeError, match="no running event loop"):
            asyncio.get_running_loop()
        return super().authorize(stage, unit_key, input_revision, resource_generation)

    def complete(
        self, permit: RobotPermit, outcome: OperationOutcome = "completed", reason: str = ""
    ) -> None:
        with pytest.raises(RuntimeError, match="no running event loop"):
            asyncio.get_running_loop()
        super().complete(permit, outcome, reason)


def test_admission_bookkeeping_stays_outside_playwright_asyncio_loop() -> None:
    admission = AsyncCheckingAdmission()

    async def browser_unit() -> None:
        with robot_operation(admission, "source_browser", "private-request"):
            await asyncio.sleep(0)
            admission.enabled = False

    asyncio.run(browser_unit())
    assert admission.outcomes == ["completed"]
    assert "private-request" not in admission.permits[0].unit_key
    assert len(admission.permits[0].input_revision) == 64


def test_transport_interruption_is_not_reported_as_completed() -> None:
    admission = PausingAdmission()
    with pytest.raises(ConnectionError):
        with robot_operation(admission, "source_browser", "private-request"):
            raise ConnectionError("network interrupted")
    assert admission.outcomes == ["unknown"]


def test_denied_unit_does_not_emit_an_operation_or_completion() -> None:
    admission = PausingAdmission(enabled=False)
    with pytest.raises(RobotPaused):
        with robot_operation(admission, "source_browser", "private-request"):
            raise AssertionError("Denied operation must never start")
    assert admission.permits == []
    assert admission.outcomes == []
