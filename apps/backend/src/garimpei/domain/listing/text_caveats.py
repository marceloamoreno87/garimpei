import re
from dataclasses import dataclass

from garimpei.domain.listing.listing import Evidence
from garimpei.domain.listing.text_normalization import normalize_text as normalized


@dataclass(frozen=True)
class Caveat:
    field: str
    text: str
    reason: str
    defect: bool = False


def restrictions(evidence: Evidence) -> tuple[Caveat, ...]:
    # Normalize locally to keep this module independent of condition's classifier.

    context = normalized((evidence.title or "") + " " + (evidence.description or ""))
    battery = bool(
        re.search(
            r"\b(?:notebook|laptop|portatil|bateria|iphone|celular|camera|fone|switch)\b", context
        )
    )
    mains = (
        bool(re.search(r"\b(?:tv|televisao|televisor|console|playstation|ps5|xbox)\b", context))
        and not battery
    )
    result: list[Caveat] = []
    for field, text in [
        ("title", evidence.title),
        ("description", evidence.description),
        ("condition", evidence.condition),
    ]:
        if text:
            result.extend(_field(field, text, battery, mains))
    return tuple(result)


def _field(field: str, text: str, battery: bool, mains: bool) -> tuple[Caveat, ...]:

    found = []
    for match in re.finditer(r"[^.!?]+[.!?]?", text):
        phrase = match.group().strip()
        value = normalized(phrase)
        if re.match(r"^(?:o |a )?(?:controle|carregador|cabo|acessorio)\b", value):
            continue
        if re.search(
            r"\b(?:desliga sozinho|desligando sozinho|reinicia sozinho|nao segura carga)\b", value
        ):
            found.append(Caveat(field, phrase, "functional_failure", True))
            continue
        if re.search(r"\b(?:nao (?:foi |esta |foram )?testad[oa]|nao testei|sem testar)\b", value):
            found.append(Caveat(field, phrase, "not_tested"))
            continue
        if (
            re.search(r"\bso (?:funciona (?:conectado |ligado )?(?:na |a )?|na )tomada\b", value)
            and not mains
        ):
            found.append(
                Caveat(
                    field,
                    phrase,
                    "abnormal_power_restriction" if battery else "power_context_unknown",
                    battery,
                )
            )
    return tuple(found)
