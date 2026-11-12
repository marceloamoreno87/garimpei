import logging
from uuid import uuid4

import pytest
from django.test import Client

from garimpei.domain.listing.condition_ports import ConditionError, ConditionSaveFailed
from garimpei.usecase.listing.classify_condition_usecase import ClassifyConditionUseCase
from garimpei.usecase.listing.read_condition_usecase import ReadConditionUseCase


def test_condition_read_failure_has_recovery_and_structured_log(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    def fail_read(*_: object) -> None:
        raise ConditionError()

    monkeypatch.setattr(ReadConditionUseCase, "execute", fail_read)
    with caplog.at_level(logging.WARNING):
        response = Client().get(f"/ofertas/{uuid4()}/")
    assert response.status_code == 503
    assert "Recarregar detalhes" in response.content.decode()
    assert any(
        getattr(record, "error_code", None) == "CONDITION_UNAVAILABLE" for record in caplog.records
    )


def test_condition_failed_write_and_read_require_reload(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_read(*_: object) -> None:
        raise ConditionError()

    def fail_write(*_: object) -> None:
        raise ConditionSaveFailed()

    monkeypatch.setattr(ReadConditionUseCase, "execute", fail_read)
    monkeypatch.setattr(ClassifyConditionUseCase, "execute", fail_write)
    response = Client().post(f"/ofertas/{uuid4()}/condicao/", {"choice": "good", "revision": "0"})
    assert response.status_code == 503
    body = response.content.decode()
    assert "Recarregue os detalhes antes" in body
    assert "data-condition-form" not in body
