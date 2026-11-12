import re
from dataclasses import dataclass
from typing import Literal

from garimpei.domain.listing.assessment import Assessment
from garimpei.domain.listing.listing import Evidence
from garimpei.domain.listing.text_caveats import restrictions
from garimpei.domain.listing.text_normalization import normalize_text

Condition = Literal["good", "defect", "uncertain"]
Choice = Literal["good", "defect"]
Tab = Literal["funcionam", "defeitos", "incerta"]
GOOD = frozenset(
    {
        "funciona bem",
        "funciona perfeitamente",
        "funcionando perfeitamente",
        "todas as funcoes funcionam",
        "o aparelho funciona perfeitamente",
    }
)
DEFECT = frozenset(
    {
        "com defeito",
        "com defeitos",
        "defeituoso",
        "o aparelho esta com defeito",
        "precisa de reparo",
        "para conserto",
        "para pecas",
        "vendo para pecas",
        "nao funciona",
        "nao liga",
    }
)


@dataclass(frozen=True)
class Signal:
    field: str
    text: str
    condition: Condition


@dataclass(frozen=True)
class Analysis:
    condition: Condition
    signals: tuple[Signal, ...]
    reasons: tuple[str, ...] = ()


def normalized(text: str) -> str:
    return normalize_text(text)


def _signal(field: str, text: str) -> Signal | None:
    value = normalized(text).rstrip(".!").strip()
    if "?" in text:
        return None
    if re.search(
        r"\b(?:nao sei|nao testei|nao testad[oa]|nao testado|sem testar|talvez|parece|acho|"
        r"as vezes|so na tomada|apenas na tomada|vendedor disse)\b|[\"“”]",
        value,
    ):
        return None
    if re.search(r"^(?:o |a )?(?:controle|carregador|cabo|fone)\b", value):
        return None
    negative = re.search(
        r"\b(?:nao (?:esta |estao |ta )?(?:funciona\w*|liga)|com defeitos?|defeituos\w*|"
        r"precisa de reparo|para (?:conserto|pecas))\b",
        value,
    )
    if value in DEFECT or negative:
        return Signal(field, text.strip(), "defect")
    if re.search(
        r"\b(?:nao (?:testei|testado|testada)|sem testar|talvez|parece|acho|as vezes)\b", value
    ):
        return None
    # A functioning accessory does not establish that the advertised device works.
    if re.search(
        r"\b(?:controle|carregador|cabo|fone)\b", value.split("funcion")[0]
    ) and not re.search(
        r"\b(?:console|aparelho|celular|iphone|ps5|playstation)\b", value.split("funcion")[0]
    ):
        return None
    positive = re.search(
        r"\b(?:funciona(?:ndo)? (?:bem|perfeitamente|normalmente)|testad[oa] e funcionando|"
        r"100\s*% funcional|funcionamento 100\s*%)",
        value,
    )
    if value in GOOD or positive:
        return Signal(field, text.strip(), "good")
    return None


def automatic_condition(evidence: Evidence) -> Analysis:
    signals: list[Signal] = []
    label = _signal("condition", evidence.condition or "")
    if label is not None:
        signals.append(label)
    phrases = (
        (field, match.group())
        for field, value in (
            ("title", evidence.title),
            ("description", evidence.description),
        )
        for match in re.finditer(r"[^.!?\r\n]+[.!?]*", value or "")
    )
    signals.extend(signal for field, text in phrases if (signal := _signal(field, text)))
    condition: Condition = "uncertain"
    if any(signal.condition == "good" for signal in signals):
        condition = "good"
    if any(signal.condition == "defect" for signal in signals):
        condition = "defect"
    caveats = restrictions(evidence)
    signals.extend(Signal(c.field, c.text, "defect" if c.defect else "uncertain") for c in caveats)
    if caveats and condition != "defect":
        condition = "defect" if any(c.defect for c in caveats) else "uncertain"
    return Analysis(condition, tuple(signals), tuple(c.reason for c in caveats))


@dataclass(frozen=True)
class ConditionState:
    analysis: Analysis
    manual: Choice | None = None
    revision: int = 0
    assessment: Assessment | None = None

    @property
    def effective(self) -> Condition:
        return self.manual or self.analysis.condition

    @property
    def tab(self) -> Tab:
        tabs: dict[Condition, Tab] = {
            "good": "funcionam",
            "defect": "defeitos",
            "uncertain": "incerta",
        }
        return tabs[self.effective]

    @property
    def conflict(self) -> bool:
        return self.manual is not None and self.analysis.condition not in {"uncertain", self.manual}

    @property
    def editable(self) -> bool:
        return self.manual is not None or self.analysis.condition == "uncertain"

    @property
    def satisfies_alert_condition(self) -> bool:
        return self.effective == "good" and (
            self.assessment is None
            or (self.assessment.sufficient and self.assessment.status == "complete")
        )

    @property
    def label(self) -> str:
        return {
            "good": "Funciona bem",
            "defect": "Não funciona bem",
            "uncertain": "Condição não confirmada",
        }[self.effective]

    @property
    def tab_label(self) -> str:
        return {
            "funcionam": "Funcionam bem",
            "defeitos": "Com defeito",
            "incerta": "Condição não confirmada",
        }[self.tab]
