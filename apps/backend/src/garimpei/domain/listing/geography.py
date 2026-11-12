from dataclasses import dataclass


@dataclass(frozen=True)
class Point:
    latitude: float
    longitude: float
    accuracy_m: float | None
    city: str
    state: str

    coordinates_known: bool = True
