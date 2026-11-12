from collections.abc import Callable
from datetime import timedelta
from uuid import UUID, uuid4

from django.db import transaction

from garimpei.domain.integration.facebook_login import FacebookLogin
from garimpei.domain.integration.values import IntegrationError
from garimpei.domain.valuation.ports import Clock
from garimpei.infra.persistence.integration_models import IntegrationSettings
from garimpei.infra.persistence.listing_models import CollectionState
from garimpei.infra.persistence.monitoring_unit_of_work import lock_monitoring_publication


class PostgresFacebookProfileRepository:
    def __init__(self, clock: Clock, resume: Callable[[], None]) -> None:
        self._clock, self._resume = clock, resume

    def read_login(self) -> FacebookLogin:
        row = IntegrationSettings.objects.filter(id="local", facebook_mode="profile").first()
        if row is None:
            return FacebookLogin()
        return FacebookLogin(
            row.facebook_login_request, row.facebook_login_state, row.facebook_login_requested_at
        )

    def request_login(self) -> None:
        with transaction.atomic():
            lock_monitoring_publication()
            row, _ = IntegrationSettings.objects.select_for_update().get_or_create(id="local")
            if (
                row.facebook_mode == "profile"
                and row.facebook_login_state in {"requested", "waiting", "verifying"}
                and row.facebook_login_requested_at
                and row.facebook_login_requested_at > self._clock() - timedelta(minutes=15)
            ):
                return
            row.facebook_mode = "profile"
            row.facebook_login_request = uuid4()
            row.facebook_login_requested_at = self._clock()
            row.facebook_login_state = "requested"
            row.save()
            for state in CollectionState.objects.select_related("current"):
                self._pause(state)

    def _pause(self, state: CollectionState) -> None:
        if state.current and state.current.finished_at is None:
            state.current.phase, state.current.finished_at = "superseded", self._clock()
            state.current.save(update_fields=["phase", "finished_at"])
        state.generation += 1
        state.access_suspended = True
        state.lease_until = None
        state.save()

    def confirm_login(self) -> None:
        updated = IntegrationSettings.objects.filter(
            id="local", facebook_mode="profile", facebook_login_state="waiting"
        ).update(facebook_login_state="verifying")
        if not updated:
            raise IntegrationError(
                "Abra a janela do Facebook e conclua o login antes de continuar."
            )

    def transition(self, request: UUID, phase: str) -> None:
        IntegrationSettings.objects.filter(
            id="local", facebook_mode="profile", facebook_login_request=request
        ).update(facebook_login_state=phase)

    def finish_login(self, request: UUID) -> None:
        with transaction.atomic():
            lock_monitoring_publication()
            row = (
                IntegrationSettings.objects.select_for_update()
                .filter(
                    id="local",
                    facebook_mode="profile",
                    facebook_login_request=request,
                    facebook_login_state="verifying",
                )
                .first()
            )
            if row is None:
                return
            row.facebook_login_state = "ready"
            row.facebook_saved_at = self._clock()
            row.facebook_expires_at = None
            row.save()
            self._resume()
