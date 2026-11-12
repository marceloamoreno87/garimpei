from collections.abc import Callable
from datetime import timedelta
from uuid import UUID

from garimpei.domain.integration.facebook_login import FacebookLoginBrowser, FacebookLoginRepository
from garimpei.domain.listing.ports import SourceFailure
from garimpei.domain.valuation.ports import Clock


class FacebookLoginHandler:
    """One worker owns the interactive window; the web process only persists requests."""

    def __init__(
        self,
        repository: FacebookLoginRepository,
        browser: Callable[[], FacebookLoginBrowser],
        clock: Clock,
    ) -> None:
        self._repository, self._factory, self._clock = repository, browser, clock
        self._browser: FacebookLoginBrowser | None = None
        self._request: UUID | None = None

    def execute(self) -> None:
        state = self._repository.read_login()
        if state.request != self._request:
            self.close()
        if state.request is None or state.phase not in {"requested", "waiting", "verifying"}:
            self.close()
            return
        if state.requested_at and self._clock() - state.requested_at > timedelta(minutes=15):
            self._repository.transition(state.request, "interrupted")
            self.close()
            return
        try:
            self._advance(state.request, state.phase)
        except (SourceFailure, OSError):
            self._repository.transition(state.request, "failed")
            self.close()

    def _advance(self, request: UUID, phase: str) -> None:
        if phase == "requested":
            if self._browser is None:
                self._browser = self._factory()
                self._request = request
                self._browser.open_login()
            self._repository.transition(request, "waiting")
            return
        if self._browser is None or not self._browser.login_is_open():
            self._repository.transition(request, "interrupted")
            self.close()
            return
        if phase != "verifying":
            return
        if not self._browser.verify_login():
            self._repository.transition(request, "waiting")
            return
        # Flush the profile and release Chromium's lock before allowing collection.
        self.close()
        self._repository.finish_login(request)

    def close(self) -> None:
        browser, self._browser = self._browser, None
        self._request = None
        if browser:
            browser.close()
