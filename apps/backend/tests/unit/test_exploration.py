from decimal import Decimal

import pytest

from garimpei.domain.listing.exploration import Criteria, InvalidExplorationInput, money_label


def test_context_rejects_malformed_inputs_and_normalizes_search() -> None:
    value = Criteria.parse({"q": "  CÂMERA  digital ", "pagina": "3"})
    assert value.search == "camera digital" and value.page == 3
    for values in (
        {"aba": "bad"},
        {"pagina": "-1"},
        {"pagina": "1.2"},
        {"versao": "x"},
        {"modalidade": "air"},
        {"q": "x" * 121},
        {"pagina": "9" * 100},
    ):
        with pytest.raises(InvalidExplorationInput):
            Criteria.parse(values)


def test_brl_preserves_zero_negative_and_unavailable() -> None:
    assert money_label(Decimal("0")) == "R$ 0,00"
    assert money_label(Decimal("-50")) == "−R$ 50,00"
    assert money_label(Decimal("1700")) == "R$ 1.700,00"
    assert money_label(None) == "Estimativa indisponível"
