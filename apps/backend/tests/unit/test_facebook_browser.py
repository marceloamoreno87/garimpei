from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from garimpei.config.env import load_listing_settings
from garimpei.domain.integration.facebook_login import FacebookLogin
from garimpei.infra.worker.facebook_login_handler import FacebookLoginHandler


def test_managed_session_uses_live_defaults_without_environment_cookie_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("GARIMPEI_FACEBOOK_STATE_FILE", raising=False)
    path = tmp_path / "session.json"
    path.write_text('{"cookies": [], "origins": []}')
    path.chmod(0o600)
    settings = load_listing_settings(facebook_state=path)
    assert settings.timeout == 20
    assert settings.retry_base == 15
    assert settings.interval == 60
    assert settings.facebook_state == path


@dataclass
class LoginRepository:
    state: FacebookLogin
    resumed: bool = False

    def read_login(self) -> FacebookLogin:
        return self.state

    def request_login(self) -> None:
        pass

    def confirm_login(self) -> None:
        self.state = replace(self.state, phase="verifying")

    def transition(self, request: UUID, phase: str) -> None:
        if request == self.state.request:
            self.state = replace(self.state, phase=phase)

    def finish_login(self, request: UUID) -> None:
        if request == self.state.request:
            self.resumed = True
            self.transition(request, "ready")


@dataclass
class LoginBrowser:
    opened: int = 0
    valid: bool = False
    live: bool = True
    closed: bool = False

    def open_login(self) -> None:
        self.opened += 1

    def verify_login(self) -> bool:
        return self.valid

    def login_is_open(self) -> bool:
        return self.live

    def close(self) -> None:
        self.closed = True


def test_login_requires_explicit_confirmation_and_verified_profile() -> None:
    now = datetime.now(UTC)
    repository = LoginRepository(FacebookLogin(uuid4(), "requested", now))
    browser = LoginBrowser()
    worker = FacebookLoginHandler(repository, lambda: browser, lambda: now)
    worker.execute()
    worker.execute()
    assert browser.opened == 1 and repository.state.phase == "waiting"
    assert not repository.resumed
    repository.confirm_login()
    worker.execute()
    assert repository.state.phase == "waiting" and not repository.resumed
    browser.valid = True
    repository.confirm_login()
    worker.execute()
    assert browser.closed and repository.resumed and repository.state.phase == "ready"


def test_restart_or_closed_window_never_implies_connected() -> None:
    now = datetime.now(UTC)
    repository = LoginRepository(FacebookLogin(uuid4(), "waiting", now))
    worker = FacebookLoginHandler(repository, LoginBrowser, lambda: now)
    worker.execute()
    assert repository.state.phase == "interrupted" and not repository.resumed


@pytest.mark.parametrize("expired", [False, True])
def test_closing_or_expiring_interactive_window_keeps_collection_paused(expired: bool) -> None:
    now = datetime.now(UTC)
    repository = LoginRepository(FacebookLogin(uuid4(), "requested", now))
    browser = LoginBrowser()
    worker = FacebookLoginHandler(repository, lambda: browser, lambda: now)
    worker.execute()
    if expired:
        now += timedelta(minutes=16)
    else:
        browser.live = False
    worker.execute()
    assert browser.closed and not repository.resumed
    assert repository.state.phase == "interrupted"
