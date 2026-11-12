from pathlib import Path

import pytest

from garimpei.domain.listing.ports import SourceFailure
from garimpei.infra.gateway.listing.marketplace_browser import MarketplaceBrowser
from tests.factories.condition_http import ConditionBrowser
from tests.factories.facebook_login import FacebookLoginSite, serve_facebook_login
from tests.factories.integration import integration_scenario
from tests.integration.test_collection import command, completed, configure, shell, sql, wait_for
from tests.integration.test_integrations import post


def test_real_chromium_profile_keeps_cookies_and_local_storage(tmp_path: Path) -> None:
    profile = tmp_path / "profile"
    tmp_path.chmod(0o700)
    site = FacebookLoginSite()
    with serve_facebook_login(site) as origin:
        first = MarketplaceBrowser(
            profile, 5, 500, profile=profile, login_origin=origin, profile_headless=True
        )
        try:
            first.open_login()
            assert first.login_is_open() and not first.verify_login()
            site.authorized = True
            assert first.verify_login()
            contender = MarketplaceBrowser(
                profile, 1, 500, profile=profile, login_origin=origin, profile_headless=True
            )
            try:
                with pytest.raises(SourceFailure, match="browser_session_in_use"):
                    contender.open_login()
                assert first.login_is_open()
            finally:
                contender.close()
        finally:
            first.close()
        site.authorized = False
        second = MarketplaceBrowser(
            profile, 5, 500, profile=profile, login_origin=origin, profile_headless=True
        )
        try:
            second.open_login()
            assert second.verify_login()
            assert profile.stat().st_mode & 0o777 == 0o700
        finally:
            second.close()


def test_login_request_verification_and_challenge_preserve_history(tmp_path: Path) -> None:
    site = FacebookLoginSite()
    with (
        serve_facebook_login(site) as origin,
        integration_scenario(tmp_path) as (instance, source, clock, state, credentials),
    ):
        with instance.private_file.open("a") as output:
            output.write(f"GARIMPEI_FACEBOOK_BROWSER_FIXTURE_URL={origin}\n")
        configure(instance)
        completed(instance, 1)
        initial = sql(instance, "SELECT initial_completed_at FROM runtime_collectionstate")
        browser = ConditionBrowser(instance)
        assert browser.request("/integracoes/", {"action": "facebook-browser"})[0] == 403
        assert post(browser, {"action": "facebook-browser"})[0] == 303
        wait_for(
            lambda: (
                sql(instance, "SELECT facebook_login_state FROM runtime_integrationsettings")
                == [("waiting",)]
            ),
            "interactive window waiting",
        )
        request = sql(instance, "SELECT facebook_login_request FROM runtime_integrationsettings")
        assert sql(instance, "SELECT access_suspended FROM runtime_collectionstate") == [(True,)]
        assert post(browser, {"action": "facebook-browser"})[0] == 303
        assert (
            sql(instance, "SELECT facebook_login_request FROM runtime_integrationsettings")
            == request
        )
        assert post(browser, {"action": "facebook-confirm"})[0] == 303
        wait_for(
            lambda: (
                sql(instance, "SELECT facebook_login_state FROM runtime_integrationsettings")
                == [("waiting",)]
            ),
            "invalid login remains paused",
        )
        assert sql(instance, "SELECT access_suspended FROM runtime_collectionstate") == [(True,)]
        site.authorized = True
        assert post(browser, {"action": "facebook-confirm"})[0] == 303
        wait_for(
            lambda: (
                sql(instance, "SELECT facebook_login_state FROM runtime_integrationsettings")
                == [("ready",)]
            ),
            "verified persistent profile",
        )
        completed(instance, 2)
        assert sql(instance, "SELECT initial_completed_at FROM runtime_collectionstate") == initial
        assert credentials.joinpath("facebook-browser").is_dir()
        source.mode = "access"
        clock.advance(61)
        completed(instance, 3, "partial")
        assert "O Facebook precisa da sua confirmação" in browser.request("/integracoes/")[1]
        command(instance, "./scripts/stop.sh")
        command(instance, "./scripts/init.sh", "--disposable")
        shell(
            instance,
            """
from garimpei.main import reconcile_listings
from garimpei.infra.persistence.listing_models import CollectionState
reconcile_listings(recover_access=True)
assert CollectionState.objects.get().access_suspended
""",
        )
        assert sql(instance, "SELECT initial_completed_at FROM runtime_collectionstate") == initial
