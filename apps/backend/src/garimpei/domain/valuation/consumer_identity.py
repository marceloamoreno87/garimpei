"""Small verified catalog: full TV SKUs and explicitly named headphone models."""

import re

TELEVISIONS = {
    "samsung": {"un50au7700gxzd", "un55au7700gxzd", "un50cu7700gxzd", "un55cu7700gxzd"},
    "lg": {"50ur8750psa.bwz", "55ur8750psa.bwz"},
}
HEADPHONES = {"sony": {"wh1000xm4", "wh1000xm5"}, "jbl": {"tune510bt", "tune520bt", "tune720bt"}}


def television(title: str, text: str) -> str | None:
    if re.search(r"^(?:placa|display|tela|painel|base|pe|controle|suporte|fonte)\b", title):
        return None
    if re.search(r"\b(?:para pecas|somente pecas|soundbar|com suporte|inclui suporte|kit)\b", text):
        return None
    codes = set(
        re.findall(r"\bun\d{2}[a-z]{2}\d{4}[a-z]{4}\b|\b\d{2}ur\d{4}[a-z]{3}\.[a-z]{3}\b", text)
    )
    if len(codes) != 1:
        return None
    code = next(iter(codes))
    brand = next((brand for brand, models in TELEVISIONS.items() if code in models), None)
    sizes = set(re.findall(r"\b(\d{2})\s*(?:polegadas|pol\b|[\"”])", text))
    nominal_size = code[2:4] if code.startswith("un") else code[:2]
    if brand is None or (sizes and sizes != {nominal_size}):
        return None
    return f"{brand}:tv:{code}"


def headphone(title: str, text: str) -> str | None:
    if re.search(r"^(?:almofadas?|espumas?|case|estojo|cabo|arco|carcaca|pecas?)\b", title):
        return None
    if re.search(
        r"\b(?:replica|primeira linha|similar|compativel|nao original|edicao especial|kit)\b", text
    ):
        return None
    codes = {
        re.sub(r"[-\s]", "", code)
        for code in re.findall(r"\b(?:wh[-\s]?1000xm[0-9]+[a-z]*|tune\s*\d+[a-z]+)\b", text)
    }
    if len(codes) != 1:
        return None
    code = next(iter(codes))
    brand = next((brand for brand, models in HEADPHONES.items() if code in models), None)
    return f"{brand}:headphone:{code}" if brand and re.search(r"\b" + brand + r"\b", text) else None
