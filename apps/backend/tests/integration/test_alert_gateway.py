from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from garimpei.domain.alert.alert import AlertPolicy, Binding, Delivery
from garimpei.infra.gateway.alert.waha_gateway import WahaGateway
from tests.factories.alert import WahaServer, serve_waha


def delivery() -> Delivery:
    reference = uuid4()
    return Delivery(
        reference,
        1,
        Binding("synthetic", "100@c.us", "200@c.us"),
        "Nova oferta\nRef. " + str(reference),
        datetime.now(UTC),
        None,
        False,
    )


@pytest.mark.parametrize("mode", ["confirmed", "lost", "incomplete", "lost_empty"])
def test_real_http_loss_reconciles_exact_original_message_without_post(mode: str) -> None:
    state = WahaServer(mode=mode)
    value = delivery()
    with serve_waha(state) as url:
        gateway = WahaGateway(
            url, "private-test-key", AlertPolicy(history_pages=3, history_limit=1)
        )
        assert gateway.check(value.binding)
        result = gateway.send(value)
        assert result.state == ("confirmed" if mode == "confirmed" else "uncertain")
        recovered = gateway.reconcile(value, datetime.now(UTC))
        assert recovered.state == ("uncertain" if mode == "lost_empty" else "confirmed")
        assert len([call for call in state.calls if call[0] == "POST"]) == 1
        assert any("offset=2" in call[1] for call in state.calls)


def test_pending_known_id_and_negative_history_controls() -> None:
    state = WahaServer(ack=0)
    value = delivery()
    with serve_waha(state) as url:
        gateway = WahaGateway(url, "private", AlertPolicy(history_pages=3))
        result = gateway.send(value)
        assert result.state == "uncertain" and result.receipt is not None
        known = replace(value, message_id=result.receipt.id)
        assert gateway.reconcile(known, datetime.now(UTC)).state == "uncertain"
        state.messages[0]["ack"] = 2
        assert gateway.reconcile(known, datetime.now(UTC)).state == "confirmed"
        for field, wrong in [
            ("fromMe", False),
            ("to", "other@c.us"),
            ("from", "other@c.us"),
            ("body", "wrong"),
        ]:
            original = state.messages[0][field]
            state.messages[0][field] = wrong
            assert gateway.reconcile(known, datetime.now(UTC)).state == "uncertain"
            state.messages[0][field] = original
        state.messages.append(dict(state.messages[0], id="conflict"))
        assert gateway.reconcile(value, datetime.now(UTC)).state == "uncertain"
        assert len([call for call in state.calls if call[0] == "POST"]) == 1


def test_session_identity_and_authentication_are_required() -> None:
    state = WahaServer()
    value = delivery()
    with serve_waha(state) as url:
        gateway = WahaGateway(url, "private", AlertPolicy())
        for ready, authenticated, account in [
            (False, True, "200@c.us"),
            (True, False, "200@c.us"),
            (True, True, "300@c.us"),
        ]:
            state.ready, state.authenticated, state.account = ready, authenticated, account
            assert not gateway.check(value.binding)
        assert all(method == "GET" for method, _ in state.calls)


def test_same_provider_id_with_conflicting_body_does_not_confirm() -> None:
    state = WahaServer()
    value = delivery()
    with serve_waha(state) as url:
        gateway = WahaGateway(url, "private", AlertPolicy(history_pages=3, history_limit=2))
        gateway.send(value)
        original = state.messages[0]
        state.messages[:] = [
            dict(original, body="Other content\nRef. " + str(value.reference)),
            original,
        ]
        assert gateway.reconcile(value, datetime.now(UTC)).state == "uncertain"


def test_refused_connection_is_proven_not_transmitted() -> None:
    import socket

    with socket.socket() as bound:
        bound.bind(("127.0.0.1", 0))
        port = bound.getsockname()[1]
    gateway = WahaGateway(f"http://127.0.0.1:{port}", "private", AlertPolicy())
    result = gateway.send(delivery())
    assert result.state == "safe_retry" and result.reason == "not_transmitted"
