import pytest

from garimpei.domain.listing.condition import automatic_condition
from garimpei.domain.listing.listing import Evidence


@pytest.mark.parametrize(
    ("evidence", "expected"),
    [
        (Evidence(description="FUNCIONA   PERFEITAMENTE."), "good"),
        (Evidence(condition="Com defeito"), "defect"),
        (Evidence(description="Precisa de reparo."), "defect"),
        (Evidence(description="Para peças."), "defect"),
        (Evidence(description="Funciona bem. Não liga."), "defect"),
        (Evidence(condition="Usado"), "uncertain"),
        (Evidence(), "uncertain"),
        (
            Evidence(
                condition="Como novo",
                description="Não sei se funciona bem. Controle com defeito. Funciona bem só na tomada. Funciona perfeitamente?",
            ),
            "uncertain",
        ),
        (Evidence(title="Ｏ aparelho funciona perfeitamente!"), "good"),
        (Evidence(description='O vendedor disse: "funciona bem".'), "uncertain"),
        (Evidence(description="Sem defeitos. Funciona bem, mas só na tomada."), "uncertain"),
    ],
)
def test_explicit_whole_declarations_only(evidence: Evidence, expected: str) -> None:
    assert automatic_condition(evidence).condition == expected


def test_manual_precedence_and_conflict_evidence() -> None:
    from garimpei.domain.listing.condition import ConditionState

    analysis = automatic_condition(Evidence(description="Funciona bem. Não liga."))
    state = ConditionState(analysis, "good", 2)
    assert state.effective == "good" and state.tab == "funcionam"
    assert state.conflict and state.editable and state.satisfies_alert_condition
    assert analysis.signals[1].field == "description" and analysis.signals[1].text == "Não liga."
    assert not ConditionState(automatic_condition(Evidence()), "good", 2).conflict
    assert not ConditionState(automatic_condition(Evidence(description="Funciona bem."))).editable
