"""Manual combinations use the same supported catalog as automatic F06 identity."""

from collections.abc import Mapping

from garimpei.domain.listing.condition import normalized
from garimpei.domain.listing.listing import Evidence
from garimpei.domain.valuation.identity import identify
from garimpei.domain.valuation.identity_errors import InvalidIdentityCombination

REQUIRED: dict[str, tuple[str, ...]] = {
    "playstation5": ("family", "model", "generation", "edition", "capacity"),
    "iphone": ("family", "model", "edition", "capacity"),
    "xbox": ("family", "model", "edition", "capacity"),
    "switch": ("family", "model", "generation", "capacity"),
    "graphics_card": ("family", "model", "capacity"),
    "camera": ("family", "brand", "model", "edition"),
    "television": ("family", "brand", "model"),
    "headphone": ("family", "brand", "model"),
}
ALLOWED = frozenset({key for names in REQUIRED.values() for key in names} | {"memory_type"})


def validated_values(values: Mapping[str, str]) -> tuple[tuple[str, str], ...]:
    if not values or set(values) - ALLOWED:
        raise InvalidIdentityCombination("Atributos inválidos: use somente os campos da família.")
    result = {key: normalized(value).strip() for key, value in values.items() if value.strip()}
    family = result.get("family", "")
    required = REQUIRED.get(family)
    if required is None or any(not result.get(key) for key in required):
        raise InvalidIdentityCombination("Família, modelo ou atributos determinantes ausentes.")
    if set(result) - set(required) - ({"memory_type"} if family == "graphics_card" else set()):
        raise InvalidIdentityCombination("Atributo não pertence à família informada.")
    if any(len(value) > 120 for value in result.values()):
        raise InvalidIdentityCombination("Atributo longo: esperado no máximo 120 caracteres.")
    result["capacity"] = result.get("capacity", "").replace(" ", "")
    if not result["capacity"]:
        del result["capacity"]
    key = identify(Evidence(title=product_title(result)))
    if key is None:
        raise InvalidIdentityCombination()
    return tuple(sorted(result.items()))


def product_title(values: Mapping[str, str]) -> str:
    family = values.get("family", "")
    model, capacity = values.get("model", ""), values.get("capacity", "")
    edition, generation = values.get("edition", ""), values.get("generation", "")
    if family == "playstation5" and model == "ps5":
        media = {"disc": "disco", "digital": "edição digital"}.get(edition, "invalid")
        return f"PlayStation 5 {generation} {media} {capacity}"
    if family == "iphone":
        label = {"standard": "", "promax": "pro max"}.get(edition, edition)
        return f"iPhone {model} {label} {capacity}"
    if family == "xbox":
        media = {"standard": "", "disc": "disco", "digital": "digital"}.get(edition, "invalid")
        return f"Xbox {model.replace('series', 'Series ')} {media} {capacity}"
    if family == "switch" and model == "switch":
        return f"Nintendo Switch {generation} {capacity}"
    if family == "graphics_card":
        return f"RTX {model} {capacity} {values.get('memory_type', '')}"
    if family == "camera" and edition == "body":
        return f"{values.get('brand', '')} {model} somente corpo"
    if family == "television":
        return f"TV {values.get('brand', '')} {model}"
    if family == "headphone":
        return f"Fone {values.get('brand', '')} {model}"
    return "unsupported manual combination"


def product_values(key: str) -> dict[str, str]:
    parts = key.split(":")
    if parts[:2] == ["sony", "ps5"]:
        return dict(
            family="playstation5",
            model="ps5",
            generation=parts[2],
            edition=parts[3],
            capacity=parts[4],
        )
    if parts[0] == "apple":
        return dict(
            family="iphone",
            model=parts[1].removeprefix("iphone"),
            edition=parts[2],
            capacity=parts[3],
        )
    if parts[0] == "microsoft":
        return dict(
            family="xbox", model=parts[1].removeprefix("xbox"), edition=parts[2], capacity=parts[3]
        )
    if parts[0] == "nintendo":
        return dict(family="switch", model="switch", generation=parts[2], capacity=parts[3])
    if parts[0] == "nvidia":
        result = dict(family="graphics_card", model=parts[2], capacity=parts[3])
        if len(parts) > 4:
            result["memory_type"] = parts[4]
        return result
    if parts[1] == "tv":
        return dict(family="television", brand=parts[0], model=parts[2])
    if parts[1] == "headphone":
        return dict(family="headphone", brand=parts[0], model=parts[2])
    return dict(family="camera", brand=parts[0], model=parts[2], edition="body")
