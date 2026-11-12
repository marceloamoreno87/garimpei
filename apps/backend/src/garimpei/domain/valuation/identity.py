import re

from garimpei.domain.listing.condition import normalized
from garimpei.domain.listing.listing import Evidence
from garimpei.domain.valuation.component_identity import camera, graphics_card
from garimpei.domain.valuation.consumer_identity import headphone, television
from garimpei.domain.valuation.electronics_identity import iphone, switch, xbox


def identify(evidence: Evidence) -> str | None:
    text = normalized((evidence.title or "") + " " + (evidence.description or ""))
    title = normalized(evidence.title or "")
    if re.search(
        r"^(?:capa|capinha|pelicula|carregador|controle|jogo|suporte|lente|pecas?)\b|\blote\b",
        title,
    ):
        return None
    if re.search(r"\b[2-9]\s*(?:unidades|consoles|aparelhos|ps5|playstation)\b", text):
        return None
    camera_identity = camera(text)
    television_identity = television(title, text)
    headphone_identity = headphone(title, text)
    families = sum(
        bool(re.search(pattern, text))
        for pattern in (
            r"\b(?:playstation\s*5|ps5)\b",
            r"\biphone\s*\d+\b",
            r"\bxbox\s*series\s*[sx]\b",
            r"\bnintendo\s*switch\b",
            r"\brtx\s*\d{4}\b",
        )
    )
    if families + bool(camera_identity) + bool(television_identity) + bool(headphone_identity) > 1:
        return None
    if re.search(r"\brtx\s*\d{4}\b", text):
        return graphics_card(text)
    if television_identity is not None:
        return television_identity
    if headphone_identity is not None:
        return headphone_identity
    if camera_identity is not None:
        return camera_identity
    if re.search(r"\bxbox\s*series\s*[sx]\b", text):
        return xbox(text)
    if re.search(r"\bnintendo\s*switch\b", text):
        return switch(text)
    console = re.search(r"\b(playstation\s*5|ps5)\b", text)
    phone = re.search(r"\biphone\s*(11|12|13|14|15|16)\b", text)
    if console and phone:
        return None
    if phone:
        return iphone(text)
    if not console:
        return None
    if re.search(r"\bcfi[- ]?2114a\b", text):
        return _validated_cfi(text)
    return _playstation(text)


def _playstation(text: str) -> str | None:
    generations = {name for name in ("slim", "fat", "pro") if re.search(r"\b" + name + r"\b", text)}
    capacities = {
        re.sub(r"\s", "", value).replace("tera", "tb")
        for value in re.findall(r"(?<!\d)(825\s*gb|1\s*tb|1\s*tera|2\s*tb)", text)
    }
    physical = bool(
        re.search(r"com leitor|c/\s*leitor|midia fisica|versao disco|\bdisco\b|\bdisk\b", text)
    )
    digital = bool(re.search(r"slim\s+digital|edicao digital|midia digital|digital edition", text))
    if len(generations) != 1 or len(capacities) != 1 or physical == digital:
        return None
    if re.search(r"edicao (limitada|especial)", text):
        return None
    return f"sony:ps5:{next(iter(generations))}:{'disc' if physical else 'digital'}:{next(iter(capacities))}"


def _validated_cfi(text: str) -> str | None:
    conflict = re.search(
        r"\b(fat|pro|825\s*gb|2\s*tb)\b|edicao digital|slim digital|midia digital", text
    )
    return None if conflict else "sony:ps5:slim:disc:1tb"
