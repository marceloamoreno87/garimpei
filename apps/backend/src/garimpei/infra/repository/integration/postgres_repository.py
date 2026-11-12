from datetime import UTC, datetime
from pathlib import Path

from django.db import DatabaseError, transaction

from garimpei.domain.integration.values import (
    FacebookSession,
    Group,
    IntegrationConfiguration,
    IntegrationUnavailable,
)
from garimpei.domain.valuation.ports import Clock
from garimpei.infra.persistence.integration_models import IntegrationSettings
from garimpei.infra.persistence.listing_models import CollectionState
from garimpei.infra.persistence.monitoring_models import MonitoringConfiguration
from garimpei.infra.persistence.monitoring_unit_of_work import lock_monitoring_publication
from garimpei.infra.repository.integration.private_session import current_path, write_session


class PostgresIntegrationRepository:
    def __init__(self, directory: Path, clock: Clock) -> None:
        self._directory, self._clock = directory, clock

    def read(self) -> IntegrationConfiguration:
        row = IntegrationSettings.objects.filter(id="local").first()
        if row is None:
            return IntegrationConfiguration()
        return IntegrationConfiguration(
            row.facebook_revision,
            row.facebook_saved_at,
            row.facebook_expires_at,
            self._facebook_phase(row),
            row.whatsapp_configured,
            row.whatsapp_session,
            row.whatsapp_account,
            row.whatsapp_group,
            row.whatsapp_group_name,
            row.alerts_enabled,
            row.facebook_mode,
            row.facebook_login_state,
        )

    def facebook_path(self) -> Path | None:
        row = IntegrationSettings.objects.filter(id="local").first()
        if row is None or not row.facebook_revision:
            return None
        path = current_path(self._directory, row.facebook_file)
        if path is None:
            raise IntegrationUnavailable()
        return path

    def _facebook_phase(self, row: IntegrationSettings) -> str:
        if row.facebook_mode == "profile":
            return self._profile_phase(row)
        if not row.facebook_revision:
            return "missing"
        if current_path(self._directory, row.facebook_file) is None:
            return "missing_file"
        if row.facebook_expires_at and row.facebook_expires_at <= self._clock():
            return "expired"
        active = MonitoringConfiguration.objects.filter(slot="active").values_list("id", flat=True)
        state = (
            CollectionState.objects.select_related("current")
            .filter(configuration_id__in=active)
            .first()
        )
        if state and state.access_suspended:
            results = state.current.results.values() if state.current else ()
            reasons = {item.get("reason") for item in results if isinstance(item, dict)}
            return "challenge" if "session_challenge" in reasons else "expired"
        if (
            state
            and row.facebook_saved_at
            and state.last_success_at
            and state.last_success_at >= row.facebook_saved_at
            and state.current_id != row.facebook_baseline_cycle
            and state.current is not None
            and state.current.phase == "complete"
        ):
            return "connected"
        return "pending"

    def _profile_phase(self, row: IntegrationSettings) -> str:
        if row.facebook_login_state != "ready":
            return "browser_" + (row.facebook_login_state or "interrupted")
        if not (self._directory / "facebook-browser").is_dir():
            return "browser_interrupted"
        if CollectionState.objects.filter(access_suspended=True).exists():
            return "browser_challenge"
        return "connected"

    def save_facebook(self, session: FacebookSession) -> None:
        path: Path | None = None
        try:
            with transaction.atomic():
                lock_monitoring_publication()
                row, _ = IntegrationSettings.objects.select_for_update().get_or_create(id="local")
                path = write_session(self._directory, row.facebook_revision + 1, session)
                self._save_session(row, path, session)
        except (DatabaseError, OSError):
            if path:
                path.unlink(missing_ok=True)
            raise IntegrationUnavailable() from None

    def _save_session(self, row: IntegrationSettings, path: Path, session: FacebookSession) -> None:
        expires = [
            item.expires
            for item in session.cookies
            if item.name in {"c_user", "xs"} and item.expires > 0
        ]
        active = MonitoringConfiguration.objects.filter(slot="active").values_list("id", flat=True)
        baseline = CollectionState.objects.filter(configuration_id__in=active).first()
        row.facebook_baseline_cycle = baseline.current_id if baseline else None
        row.facebook_mode = "cookies"
        row.facebook_login_state = ""
        row.facebook_login_request = None
        row.facebook_revision += 1
        row.facebook_file = path.name
        row.facebook_saved_at = self._clock()
        row.facebook_expires_at = datetime.fromtimestamp(min(expires), UTC) if expires else None
        row.save()
        self.resume_collections()

    def resume_collections(self) -> None:
        states = CollectionState.objects.select_related("current").all()
        for state in states:
            self._resume(state)

    def _resume(self, state: CollectionState) -> None:
        if state.current and state.current.finished_at is None:
            state.current.phase = "superseded"
            state.current.finished_at = self._clock()
            state.current.save(update_fields=["phase", "finished_at"])
        state.generation += 1
        state.access_suspended = False
        state.lease_until = None
        state.next_attempt_at = self._clock()
        state.save()

    def configure_whatsapp(self, session: str, account: str, group: Group, enabled: bool) -> None:
        with transaction.atomic():
            row, _ = IntegrationSettings.objects.select_for_update().get_or_create(id="local")
            row.whatsapp_configured = True
            row.whatsapp_session, row.whatsapp_account = session, account
            row.whatsapp_group, row.whatsapp_group_name = group.id, group.name
            row.alerts_enabled = enabled
            row.save()

    def disable_whatsapp(self) -> None:
        IntegrationSettings.objects.filter(id="local").update(alerts_enabled=False)
