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
