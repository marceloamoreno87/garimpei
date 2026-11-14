import re

import pytest
from django.http import HttpRequest, HttpResponse
from django.template.loader import render_to_string
from django.test import Client, RequestFactory
from django.urls import resolve

from garimpei.domain.navigation.ports import InvalidNavigation


@pytest.mark.parametrize(
    ("path", "current"),
    [
        ("/ofertas/", "/ofertas/"),
        ("/ofertas/00000000-0000-0000-0000-000000000001/", "/ofertas/"),
        ("/acompanhamento/", "/acompanhamento/"),
        ("/acompanhamento/backups/", "/acompanhamento/"),
        ("/acompanhamento/robo/", "/acompanhamento/"),
        ("/acompanhamento/robo/ligar/", "/acompanhamento/"),
        ("/sugestoes/", "/sugestoes/"),
        ("/configuracoes/", "/configuracoes/"),
        ("/configuracao/regiao/", "/configuracoes/"),
        ("/integracoes/", "/integracoes/"),
        ("/integracoes/ia/", "/integracoes/ia/"),
        ("/ofertas/00000000-0000-0000-0000-000000000001/ia/", "/ofertas/"),
        ("/ofertas/00000000-0000-0000-0000-000000000001/ia/reavaliar/", "/ofertas/"),
        ("/integracoes/ia/cobertura/", "/integracoes/ia/"),
        ("/acompanhamento/ia/explicar/", "/acompanhamento/"),
    ],
)
def test_navigation_identifies_the_current_destination(path: str, current: str) -> None:
    request = RequestFactory().get(path)
    request.resolver_match = resolve(path)
    body = render_to_string("monitoring/layout.html", request=request)
    navigation = re.search(
        r'<nav\b[^>]*aria-label="Navegação principal"[^>]*>(.*?)</nav>', body, re.S
    )
    assert navigation is not None
    links = re.findall(r"<a\b([^>]+)>", navigation[1])
    selected = [attributes for attributes in links if 'aria-current="page"' in attributes]
    assert len(selected) == 1
    assert f'href="{current}"' in selected[0]
    assert 'href="/sugestoes/"' in navigation[1]
    assert 'href="/integracoes/ia/"' in navigation[1]
    assert "São Paulo" not in body


class InvalidSuggestionsHandler:
    def handle(self, request: HttpRequest, action: str = "status") -> HttpResponse:
        raise InvalidNavigation


def test_invalid_suggestions_page_has_context_and_recovery(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("garimpei.main.build_navigation_handler", InvalidSuggestionsHandler)

    response = Client().get("/sugestoes/?pagina=0")
    assert response.status_code == 400
    body = response.content.decode()
    assert "<main" in body and "<h1>" in body
    assert 'href="/sugestoes/"' in body
