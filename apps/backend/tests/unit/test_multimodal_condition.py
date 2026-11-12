import pytest

from garimpei.domain.listing.assessment import Assessment, Finding, Reference
from garimpei.domain.listing.assessment_policy import decide
from garimpei.domain.listing.condition import ConditionState, automatic_condition
from garimpei.domain.listing.listing import Evidence


@pytest.mark.parametrize(
    ("title", "text", "expected"),
    [
        (
            "PlayStation 5",
            "Funciona perfeitamente, mas desliga sozinho depois de dez minutos",
            "defect",
        ),
        (
            "Notebook portátil com bateria",
            "Funciona perfeitamente, mas só funciona conectado na tomada",
            "defect",
        ),
        ("Câmera Canon T5i", "Não foi testado. Funciona perfeitamente.", "uncertain"),
        ("TV Samsung", "Funciona perfeitamente, mas só funciona conectado na tomada", "good"),
        ("Aparelho", "Funciona perfeitamente, mas só funciona conectado na tomada", "uncertain"),
        ("PlayStation 5", "O controle não liga. O console funciona perfeitamente.", "good"),
    ],
)
def test_text_restrictions_preserve_main_item_context_without_model(
    title: str, text: str, expected: str
) -> None:
    result = automatic_condition(Evidence(title=title, description=text))
    assert result.condition == expected
    if expected != "good":
        assert result.reasons
        assert any(signal.text in text for signal in result.signals)


@pytest.mark.parametrize(
    ("kind", "expected", "sufficient"),
    [
        ("light_wear", "good", True),
        ("clear_defect", "defect", True),
        ("suspected", "uncertain", False),
        ("unknown", "uncertain", False),
    ],
)
def test_condition_is_decided_from_traceable_evidence_not_a_model_class(
    kind: str, expected: str, sufficient: bool
) -> None:
    finding = Finding(
        "appearance", kind, "Sinal da carcaça", (Reference("image", photo_id="p", sha256="a" * 64),)
    )
    result = decide(
        Evidence(description="O aparelho funciona perfeitamente."),
        "computer",
        (finding,),
        complete=True,
    )
    assert result.condition == expected and result.sufficient is sufficient


def test_photos_pending_and_manual_good_cannot_authorize_alert() -> None:
    evidence = Evidence(description="O aparelho funciona perfeitamente.")
    result = decide(evidence, "computer", (), complete=False, reason="waiting_inference")
    state = ConditionState(
        automatic_condition(evidence), "good", 2, Assessment(reason=result.reason)
    )
    assert state.effective == "good" and state.tab == "funcionam"
    assert not state.satisfies_alert_condition


def test_negative_text_survives_missing_photos_and_unknown_category() -> None:
    result = decide(
        Evidence(description="O aparelho não liga."),
        "unknown",
        (),
        complete=False,
        reason="no_photos",
    )
    assert result.condition == "defect" and not result.sufficient
