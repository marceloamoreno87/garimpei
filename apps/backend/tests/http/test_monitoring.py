import pytest
from django.test import Client

from garimpei.usecase.monitoring.read_form_usecase import MonitoringForm, ReadMonitoringFormUseCase


def test_setup_region_is_a_real_form(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ReadMonitoringFormUseCase, "execute", lambda _: MonitoringForm())
    response = Client().get("/configuracao/regiao/")
    assert response.status_code == 200
    assert b'name="cep"' in response.content
    assert b"csrfmiddlewaretoken" in response.content
