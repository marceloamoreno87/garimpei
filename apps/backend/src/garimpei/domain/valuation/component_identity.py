"""Conservative identities for standalone graphics cards and explicitly bare camera bodies."""

import re

CAMERA_MODELS = {
    "canon": r"\b(?:eos\s*)?(t5i|t6i|t7i|sl2|sl3|80d|90d)\b",
    "nikon": r"\b(d3300|d3500|d5300|d5600|d7100|d7200|d750)\b",
    "sony": r"\b(a6000|a6300|a6400)\b",
}
RTX_MEMORY = {
    "2060": {"6", "12"},
    "3060": {"8", "12"},
    "3060ti": {"8"},
    "3070": {"8"},
    "3080": {"10", "12"},
    "4060": {"8"},
    "4060ti": {"8", "16"},
    "4070": {"12"},
    "4070super": {"12"},
    "4070ti": {"12"},
    "4070tisuper": {"16"},
}


def camera(text: str) -> str | None:
    brands = {brand for brand in CAMERA_MODELS if re.search(r"\b" + brand + r"\b", text)}
    if len(brands) != 1 or not re.search(
        r"somente corpo|apenas corpo|so (?:o )?corpo|body only|corpo sem lente", text
    ):
        return None
    if re.search(r"\d+\s*[-–]\s*\d+\s*mm|\bkit\b", text):
        return None
    brand = next(iter(brands))
    models = set(re.findall(CAMERA_MODELS[brand], text))
    if len(models) != 1:
        return None
    family = {"canon": "eos", "nikon": "d", "sony": "alpha"}[brand]
    return f"{brand}:{family}:{next(iter(models))}:body"


def graphics_card(text: str) -> str | None:
    if re.search(r"\b(?:notebook|laptop|desktop|computador|pc gamer|kit|lote)\b", text):
        return None
    models = {
        re.sub(r"\s", "", m)
        for m in re.findall(r"\brtx\s*(\d{4}\s*(?:ti\s*super|super|ti)?)\b", text)
    }
    capacities = set(re.findall(r"(?<!\d)([0-9]{1,2})\s*gb\b", text))
    if len(models) != 1 or len(capacities) != 1:
        return None
    model, capacity = next(iter(models)), next(iter(capacities))
    if capacity not in RTX_MEMORY.get(model, set()):
        return None
    if re.search(r"\b(?:mobile|max[- ]?q|engenharia|modificada|recondicionada)\b", text):
        return None
    # These models have documented GDDR6 and GDDR6X variants at equal capacity.
    if model in {"3060ti", "4070"}:
        memory = set(re.findall(r"\bgddr\s*(6x?)\b", text))
        if len(memory) != 1:
            return None
        return f"nvidia:rtx:{model}:{capacity}gb:gddr{next(iter(memory))}"
    return f"nvidia:rtx:{model}:{capacity}gb"
