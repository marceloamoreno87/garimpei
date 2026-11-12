import json
import re
from pathlib import Path
from urllib.request import urlopen

import pytest

from tests.factories.condition_http import ConditionBrowser
from tests.factories.integration import integration_scenario
from tests.integration.test_collection import command, completed, configure, shell, sql, wait_for


def post(browser: ConditionBrowser, values: dict[str, str]) -> tuple[int, str, str]:
    status, body, _ = browser.request("/integracoes/")
    assert status == 200, body
    match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', body)
    assert match
    return browser.request("/integracoes/", dict(values, csrfmiddlewaretoken=match[1]))


def test_cookie_privacy_renewal_and_expiration_notice(tmp_path: Path) -> None:
    with integration_scenario(tmp_path) as (instance, source, clock, state, credentials):
        browser = ConditionBrowser(instance)
        status, body, _ = browser.request("/integracoes/")
        assert status == 200 and "Cookies do Facebook" in body
        assert (
            browser.request(
                "/integracoes/",
                {"action": "facebook", "cookies": "c_user=123; xs=synthetic-secret"},
            )[0]
            == 403
        )
        status, body, _ = post(browser, {"action": "facebook", "cookies": "private-invalid-cookie"})
        assert status == 400 and "private-invalid-cookie" not in body
        assert (
            post(browser, {"action": "facebook", "cookies": "c_user=123; xs=synthetic-secret"})[0]
            == 303
        )
        path = next(credentials.glob("facebook-*.json"))
        assert path.stat().st_mode & 0o777 == 0o600
        assert credentials.stat().st_mode & 0o777 == 0o700
        assert json.loads(path.read_text())["cookies"][1]["value"] == "synthetic-secret"
        assert "synthetic-secret" not in browser.request("/integracoes/")[1]
        assert "aguardando verificação" in browser.request("/integracoes/")[1].casefold()
        with urlopen(f"http://127.0.0.1:{instance.config.web_port}/integracoes/") as r:
            assert r.headers["Cache-Control"] == "no-store"
            assert r.headers["Referrer-Policy"] == "same-origin"
        configure(instance)
        completed(instance, 1)
        wait_for(
            lambda: "Sessão verificada" in browser.request("/integracoes/")[1],
            "verified Facebook status",
        )
        initial = sql(instance, "SELECT initial_completed_at FROM runtime_collectionstate")
        source.mode = "access"
        clock.advance(61)
        completed(instance, 2, "partial")
        wait_for(
            lambda: (
                "sessão do Facebook expirou" in browser.request("/integracoes/facebook/status/")[1]
            ),
            "expiry warning",
        )
        assert "Renovar cookies" in browser.request("/acompanhamento/")[1]
        source.mode = "initial"
        assert (
            post(browser, {"action": "facebook", "cookies": "c_user=123; xs=replacement-secret"})[0]
            == 303
        )
        assert len(list(credentials.glob("facebook-*.json"))) == 2
        assert json.loads(path.read_text())["cookies"][1]["value"] == "synthetic-secret"
        completed(instance, 3)
        assert sql(instance, "SELECT initial_completed_at FROM runtime_collectionstate") == initial
        assert sql(instance, "SELECT access_suspended FROM runtime_collectionstate") == [(False,)]
        assert sql(
            instance, "SELECT count(*) FROM runtime_alertintent WHERE state='confirmed'"
        ) == [(0,)]
        for log in ("web.log", "worker.log"):
            text = (instance.config.directory / log).read_text()
            assert "synthetic-secret" not in text and "replacement-secret" not in text
        print("HTTP-COOKIES-01 WRK-ACESSO-01/02 PASS")


def test_connect_qr_group_validation_and_persistence(tmp_path: Path) -> None:
    with integration_scenario(tmp_path) as (instance, source, clock, state, credentials):
        browser = ConditionBrowser(instance)
        assert post(browser, {"action": "connect"})[0] == 303
        assert state.present and state.phase == "SCAN_QR_CODE"
        assert "Conecte pelo seu celular" in browser.request("/integracoes/")[1]
        with urlopen(f"http://127.0.0.1:{instance.config.web_port}/integracoes/whatsapp/qr/") as r:
            assert (
                r.headers["Content-Type"] == "image/png"
                and r.headers["Cache-Control"] == "no-store"
            )
            assert r.read().startswith(b"\x89PNG")
        state.phase = "WORKING"
        with urlopen(
            f"http://127.0.0.1:{instance.config.web_port}/integracoes/whatsapp/status/?expected=STOPPED"
        ) as response:
            assert response.headers.get("HX-Refresh") == "true"
        status, body, _ = browser.request("/integracoes/")
        assert status == 200 and "Garimpo de teste" in body
        assert (
            post(
                browser,
                {"action": "whatsapp", "group": "999@g.us", "account": "200@c.us", "enabled": "on"},
            )[0]
            == 400
        )
        assert (
            post(
                browser,
                {"action": "whatsapp", "group": "12345@g.us", "account": "wrong", "enabled": "on"},
            )[0]
            == 400
        )
        assert (
            post(
                browser,
                {
                    "action": "whatsapp",
                    "group": "12345@g.us",
                    "account": "200@c.us",
                    "enabled": "on",
                },
            )[0]
            == 303
        )
        assert sql(
            instance, "SELECT whatsapp_group,alerts_enabled FROM runtime_integrationsettings"
        ) == [("12345@g.us", True)]
        assert not state.messages
        state.account = "201@c.us"
        assert (
            post(
                browser,
                {
                    "action": "whatsapp",
                    "group": "54321-123@g.us",
                    "account": "200@c.us",
                    "enabled": "on",
                },
            )[0]
            == 400
        )
        assert sql(instance, "SELECT whatsapp_group FROM runtime_integrationsettings") == [
            ("12345@g.us",)
        ]
        state.account = "200@c.us"
        command(instance, "./scripts/stop.sh")
        command(instance, "./scripts/init.sh", "--disposable")
        assert "Grupo salvo" in browser.request("/integracoes/")[1]
        assert post(browser, {"action": "disable"})[0] == 303
        assert sql(instance, "SELECT alerts_enabled FROM runtime_integrationsettings") == [(False,)]
        assert not state.messages
        print("HTTP-WHATSAPP-01 HTTP-GRUPOS-01 PASS")


def test_group_delivery_uses_selected_binding_and_verifies_gows_receipt(tmp_path: Path) -> None:
    from datetime import UTC, datetime
    from uuid import uuid4

    from garimpei.domain.alert.alert import AlertPolicy, Binding, Delivery
    from garimpei.infra.gateway.alert.waha_gateway import WahaGateway
    from tests.factories.integration import SessionServer, serve_session

    state = SessionServer(present=True, phase="WORKING")
    with serve_session(state) as url:
        gateway = WahaGateway(url, "synthetic-key", AlertPolicy(history_pages=3))
        reference = uuid4()
        delivery = Delivery(
            reference,
            1,
            Binding("default", "12345@g.us", state.account),
            "Nova oferta\nRef. " + str(reference),
            datetime.now(UTC),
            None,
            False,
        )
        assert gateway.check(delivery.binding)
        sent = gateway.send(delivery)
        assert sent.state == "confirmed" and sent.receipt is not None
        assert sent.receipt.chat == "12345@g.us"
        assert gateway.reconcile(delivery, datetime.now(UTC)).state == "confirmed"
        state.messages[0]["participant"] = "other@c.us"
        state.messages[0]["to"] = "other@c.us"
        assert gateway.reconcile(delivery, datetime.now(UTC)).state == "uncertain"
        assert len([x for x in state.calls if x[0] == "POST"]) == 1


@pytest.mark.parametrize("recipient", ["100@lid", "12345@g.us"])
def test_gows_sender_alias_confirms_only_the_bound_account_and_chat(recipient: str) -> None:
    from datetime import UTC, datetime
    from uuid import uuid4

    from garimpei.domain.alert.alert import AlertPolicy, Binding, Delivery
    from garimpei.infra.gateway.alert.waha_gateway import WahaGateway
    from tests.factories.integration import SessionServer, serve_session

    state = SessionServer(present=True, phase="WORKING", receipt_shape="gows_lid")
    with serve_session(state) as url:
        gateway = WahaGateway(url, "synthetic-key", AlertPolicy(history_pages=3))
        reference = uuid4()
        delivery = Delivery(
            reference,
            1,
            Binding("default", recipient, state.account),
            "Synthetic proof\nRef. " + str(reference),
            datetime.now(UTC),
            None,
            False,
        )
        assert gateway.send(delivery).state == "confirmed"
        assert gateway.reconcile(delivery, datetime.now(UTC)).state == "confirmed"
        message = state.messages[0]
        from typing import cast

        info = cast(dict[str, dict[str, object]], message["_data"])["Info"]
        info["SenderAlt"] = "300@s.whatsapp.net"
        assert gateway.reconcile(delivery, datetime.now(UTC)).state == "uncertain"
        info["SenderAlt"] = "200@s.whatsapp.net"
        info["Chat"] = "other@g.us"
        assert gateway.reconcile(delivery, datetime.now(UTC)).state == "uncertain"
        info["Chat"] = recipient
        message["participant"] = "other@lid"
        assert gateway.reconcile(delivery, datetime.now(UTC)).state == "uncertain"
        assert len([x for x in state.calls if x[0] == "POST"]) == 1


def test_selected_group_drives_real_worker_event_and_preserves_old_destination(
    tmp_path: Path,
) -> None:
    from tests.factories.alert_scenario import wait_alerts
    from tests.factories.integration import SessionServer, serve_session
    from tests.factories.listing import serve
    from tests.factories.valuation import (
        ValuationSource,
        listing,
        prepare_valuation_instance,
        wait_valuation,
    )

    source = ValuationSource()
    source.rows["699"]["description"] = "Com defeito. Não funciona."
    state = SessionServer(present=True, phase="WORKING")
    with serve(source) as url, serve_session(state) as waha:
        instance, clock = prepare_valuation_instance(
            Path(__file__).resolve().parents[4], tmp_path, url
        )
        with instance.private_file.open("a") as output:
            output.write(
                f"GARIMPEI_ALERT_FIXTURE_URL={waha}\nGARIMPEI_INTEGRATION_PRIVATE_DIR={tmp_path / 'private-session'}\n"
            )
        command(instance, "./scripts/init.sh", "--disposable")
        try:
            configure(instance)
            completed(instance, 1)
            wait_valuation(instance, price="2300.00")
            browser = ConditionBrowser(instance)
            assert (
                post(
                    browser,
                    {
                        "action": "whatsapp",
                        "group": "12345@g.us",
                        "account": "200@c.us",
                        "enabled": "on",
                    },
                )[0]
                == 303
            )
            clock.advance(1)
            source.rows["981"] = listing(
                "981",
                "1000,00",
                published_at=clock.value.isoformat(),
                delivery=True,
                delivery_cep="01001000",
                pickup=False,
            )
            clock.advance(61)
            completed(instance, 2)
            wait_alerts(instance, 1, clock)
            assert len(state.messages) == 1 and state.messages[0]["from"] == "12345@g.us"
            old = sql(
                instance,
                "SELECT a.id,a.recipient FROM runtime_alertintent a JOIN runtime_alerteventdecision d ON a.decision_id=d.id JOIN runtime_listingevent e ON d.event_id=e.id JOIN runtime_listing l ON e.listing_id=l.id WHERE l.external_id='981' AND a.state='confirmed'",
            )
            assert len(old) == 1 and old[0][1] == "12345@g.us"
            assert (
                post(
                    browser,
                    {
                        "action": "whatsapp",
                        "group": "54321-123@g.us",
                        "account": "200@c.us",
                        "enabled": "on",
                    },
                )[0]
                == 303
            )
            clock.advance(1)
            source.rows["982"] = listing(
                "982",
                "1000,00",
                published_at=clock.value.isoformat(),
                delivery=True,
                delivery_cep="01001000",
                pickup=False,
            )
            clock.advance(61)
            completed(instance, 3)
            wait_alerts(instance, 2, clock)
            assert len(state.messages) == 2 and state.messages[1]["from"] == "54321-123@g.us"
            assert sql(
                instance,
                "SELECT recipient FROM runtime_alertintent WHERE id='" + str(old[0][0]) + "'",
            ) == [("12345@g.us",)]
            print("WRK-GRUPOS-01 integrated F03/F04/F05/F07/F09 + UI selected groups PASS")
        finally:
            command(instance, "./scripts/stop.sh", "--clean")


def test_cookie_renewal_fences_collection_already_in_flight(tmp_path: Path) -> None:
    with integration_scenario(tmp_path) as (instance, source, clock, state, credentials):
        browser = ConditionBrowser(instance)
        assert (
            post(browser, {"action": "facebook", "cookies": "c_user=123; xs=old-secret"})[0] == 303
        )
        old_path = next(credentials.glob("facebook-*.json"))
        configure(instance)
        completed(instance, 1)
        initial = sql(instance, "SELECT initial_completed_at FROM runtime_collectionstate")
        source.price, source.pause_path = "R$ 1.900,00", "/detail/101"
        clock.advance(61)
        assert source.held.wait(10)
        old_cycle = sql(instance, "SELECT current_id FROM runtime_collectionstate")[0][0]
        source.price = "R$ 2.200,00"
        assert (
            post(browser, {"action": "facebook", "cookies": "c_user=123; xs=new-secret"})[0] == 303
        )
        assert sql(
            instance, f"SELECT phase FROM runtime_collectioncycle WHERE id='{old_cycle}'"
        ) == [("superseded",)]
        shell(
            instance,
            """
from garimpei.main import _effective_listing_settings
from garimpei.infra.persistence.integration_models import IntegrationSettings
row = IntegrationSettings.objects.get(id='local')
assert _effective_listing_settings().facebook_state.name == row.facebook_file
""",
        )
        completed(instance, 3)
        source.release.set()
        wait_for(
            lambda: (
                sql(
                    instance,
                    "SELECT count(*) FROM procrastinate_jobs WHERE task_name='garimpei.collect_listings' AND status IN ('todo','doing')",
                )
                == [(0,)]
            ),
            "old collection task returned after renewed session",
        )
        assert sql(instance, "SELECT price FROM runtime_listingobservation WHERE price=1900") == []
        assert sql(instance, "SELECT initial_completed_at FROM runtime_collectionstate") == initial
        assert len(list(credentials.glob("facebook-*.json"))) == 2
        assert json.loads(old_path.read_text())["cookies"][1]["value"] == "old-secret"
        print("WRK-ACESSO-02 inflight generation fence and new session path PASS")
