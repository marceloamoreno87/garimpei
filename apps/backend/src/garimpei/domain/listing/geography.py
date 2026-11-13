from dataclasses import dataclass

MARKETPLACE_RADIUS_KM = 20


@dataclass(frozen=True)
class Point:
    latitude: float
    longitude: float
    accuracy_m: float | None
    city: str
    state: str

    coordinates_known: bool = True


# City selected in the native source, observed on 2026-11-13. This is a search
# origin, not a precise postal address or a replacement for delivery coverage.
MARKETPLACE_SEARCH_ORIGIN = Point(-23.55, -46.6333, None, "São Paulo", "SP")
