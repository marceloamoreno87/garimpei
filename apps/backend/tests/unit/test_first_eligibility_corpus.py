from copy import deepcopy

import pytest

from tests.factories.first_eligibility import first_cases, validate_first_cases


def test_contract_corpus_declares_distinct_sources_and_all_scenarios() -> None:
    cases = first_cases()
    assert set(cases) >= {
        "BASE",
        "LEGADO",
        "QUEDAS",
        "variations",
        "observation",
        "channel",
        "barrier",
    }
    assert cases["variations"]["stale"]["expected"] == "profit_observation_mismatch"
    assert cases["LEGADO"]["preserve"] == [
        "id",
        "body",
        "recipient",
        "account",
        "session",
        "confirmed_message",
        "attempts",
    ]


@pytest.mark.parametrize("bad", ["self_comparable", "money", "naive", "history", "drops"])
def test_contract_corpus_rejects_incoherent_preparation(bad: str) -> None:
    cases = deepcopy(first_cases())
    if bad == "self_comparable":
        cases["observation"]["comparables"][0] = "16001"
    elif bad == "money":
        cases["variations"]["zero"]["expected_profit"] = "1.00"
    elif bad == "naive":
        cases["BASE"]["16001"]["published_at"] = "2026-11-12T10:00:00"
    elif bad == "history":
        cases["LEGADO"]["count"] = 99
    else:
        cases["QUEDAS"]["distinct_reductions"] = 3
    with pytest.raises(AssertionError):
        validate_first_cases(cases)
