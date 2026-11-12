"""Explicit model/capacity combinations; uncertain variants never share comparables."""

import re

# Storage is built-in capacity, not an SD card or external drive.
IPHONE_CAPACITIES: dict[str, dict[str, tuple[str, ...]]] = {
    "11": {
        "standard": ("64gb", "128gb", "256gb"),
        "pro": ("64gb", "256gb", "512gb"),
        "promax": ("64gb", "256gb", "512gb"),
    },
    "12": {
        "standard": ("64gb", "128gb", "256gb"),
        "mini": ("64gb", "128gb", "256gb"),
        "pro": ("128gb", "256gb", "512gb"),
        "promax": ("128gb", "256gb", "512gb"),
    },
    "13": {
        "standard": ("128gb", "256gb", "512gb"),
        "mini": ("128gb", "256gb", "512gb"),
        "pro": ("128gb", "256gb", "512gb", "1tb"),
        "promax": ("128gb", "256gb", "512gb", "1tb"),
    },
    "14": {
        "standard": ("128gb", "256gb", "512gb"),
        "plus": ("128gb", "256gb", "512gb"),
        "pro": ("128gb", "256gb", "512gb", "1tb"),
        "promax": ("128gb", "256gb", "512gb", "1tb"),
    },
    "15": {
        "standard": ("128gb", "256gb", "512gb"),
        "plus": ("128gb", "256gb", "512gb"),
        "pro": ("128gb", "256gb", "512gb", "1tb"),
        "promax": ("256gb", "512gb", "1tb"),
    },
    "16": {
        "standard": ("128gb", "256gb", "512gb"),
        "plus": ("128gb", "256gb", "512gb"),
        "pro": ("128gb", "256gb", "512gb", "1tb"),
        "promax": ("256gb", "512gb", "1tb"),
    },
}


def storage(text: str) -> set[str]:
    return {
        re.sub(r"\s", "", value)
        for value in re.findall(r"(?<!\d)(?:64|128|256|512)\s*gb\b|(?<!\d)[12]\s*tb\b", text)
    }


def iphone(text: str) -> str | None:
    models = {
        (m[1], "".join((m[2] or "standard").split()))
        for m in re.finditer(
            r"\biphone\s*(11|12|13|14|15|16)\s*(pro\s*max|pro|mini|plus|e)?\b", text
        )
    }
    capacities = storage(text)
    if len(models) != 1 or len(capacities) != 1:
        return None
    generation, edition = next(iter(models))
    capacity = next(iter(capacities))
    if capacity not in IPHONE_CAPACITIES[generation].get(edition, ()):
        return None
    return f"apple:iphone{generation}:{edition}:{capacity}"


def xbox(text: str) -> str | None:
    models = set(re.findall(r"\bxbox\s*series\s*([sx])\b", text))
    capacities = storage(text)
    if len(models) != 1 or len(capacities) != 1:
        return None
    model, capacity = next(iter(models)), next(iter(capacities))
    if model == "s":
        return (
            f"microsoft:xboxseriess:standard:{capacity}" if capacity in {"512gb", "1tb"} else None
        )
    disc = bool(re.search(r"com leitor|midia fisica|\bdisco\b", text))
    digital = bool(re.search(r"digital|sem leitor", text))
    if disc == digital or capacity != "1tb" or re.search(r"galaxy|especial|limitad", text):
        return None
    return f"microsoft:xboxseriesx:{'disc' if disc else 'digital'}:{capacity}"


def switch(text: str) -> str | None:
    if re.search(r"\bswitch\s*2\b|desbloquead|modchip|edicao (?:especial|limitada)", text):
        return None
    models = set(re.findall(r"\bswitch\s*(oled|lite|v1|v2)?\b", text))
    if len(models) != 1:
        return None
    edition = next(iter(models))
    # Original revisions differ in battery/hardware; require an explicit revision.
    if edition not in {"oled", "lite", "v1", "v2"}:
        return None
    capacities = set(re.findall(r"(?<!\d)(32|64|128|256|512)\s*gb\b", text))
    capacity = "64" if edition == "oled" else "32"
    if capacities != {capacity}:
        return None
    return f"nintendo:switch:{edition}:{capacity}gb"
