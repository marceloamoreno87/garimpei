from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt
from typing import Literal

from garimpei.domain.listing.geography import Point
from garimpei.domain.listing.interest_match import tokens
from garimpei.domain.listing.listing import Evidence

CoverageState = Literal["confirmed", "excluded", "unknown"]


@dataclass(frozen=True)
class Coverage:
    pickup: CoverageState
    shipping: CoverageState
    distance_km: float | None
    pickup_reason: str
    shipping_reason: str
    pickup_candidate: bool = False
    shipping_candidate: bool = False
    pickup_precision: str = "unavailable"

    @property
    def pickup_label(self) -> str:
        return (
            "localização aproximada"
            if self.pickup_precision == "approximate"
            else self.pickup_reason
        )

    @property
    def shipping_label(self) -> str:
        if self.shipping_candidate and self.shipping == "unknown":
            return "entrega no CEP a confirmar"
        return self.shipping_reason

    @property
    def status(self) -> CoverageState:
        if "confirmed" in (self.pickup, self.shipping):
            return "confirmed"
        if self.pickup == self.shipping == "excluded":
            return "excluded"
        return "unknown"


def _distance(first: Point, second: Point) -> float:
    a, b = radians(first.latitude), radians(second.latitude)
    longitude = radians(second.longitude - first.longitude)
    half_chord = sin((a - b) / 2) ** 2 + cos(a) * cos(b) * sin(longitude / 2) ** 2
    return 6371.0088 * 2 * asin(sqrt(min(1.0, half_chord)))


def _pickup(origin: Point | None, evidence: Evidence) -> tuple[CoverageState, float | None, str]:
    if evidence.pickup is False:
        return "excluded", None, "pickup_unavailable"
    location = evidence.location
    if location and (tokens(location.city), location.state.upper()) != (("sao", "paulo"), "SP"):
        if location.city and location.state:
            return "excluded", None, "other_municipality"
        return "unknown", None, "location_unverified"
    if not origin or not location or not origin.coordinates_known or not location.coordinates_known:
        return "unknown", None, "location_unverified"
    distance = _distance(origin, location)
    if distance > 20 + 1e-9:
        return "excluded", distance, "outside_reference_radius"
    if origin.accuracy_m is None or location.accuracy_m is None:
        return "unknown", distance, "approximate_location"
    uncertainty = (origin.accuracy_m + location.accuracy_m) / 1000
    if distance + uncertainty <= 20 + 1e-9 and evidence.pickup is True:
        return "confirmed", distance, "within_radius"
    return "unknown", distance, "approximate_location"


def coverage(origin: Point | None, cep: str, evidence: Evidence) -> Coverage:
    if evidence.source_available is False:
        return Coverage("excluded", "excluded", None, "listing_unavailable", "listing_unavailable")
    pickup, distance, reason = _pickup(origin, evidence)
    if evidence.delivery_cep == cep and evidence.delivery is not None:
        shipping: CoverageState = "confirmed" if evidence.delivery else "excluded"
        shipping_reason = "destination_verified"
    else:
        shipping = "unknown"
        shipping_reason = "destination_unverified"
    offered = evidence.shipping_offered is True or evidence.delivery is True
    shipping_candidate = shipping == "confirmed" or (offered and shipping != "excluded")
    location = evidence.location
    municipality = location is not None and (tokens(location.city), location.state.upper()) == (
        ("sao", "paulo"),
        "SP",
    )
    pickup_candidate = pickup == "confirmed" or (
        municipality
        and evidence.pickup is True
        and pickup != "excluded"
        and (distance is not None or evidence.pickup_scope_verified is True)
    )
    precision = "unavailable"
    if distance is not None or evidence.pickup_scope_verified is True:
        precision = "precise" if pickup == "confirmed" else "approximate"
    return Coverage(
        pickup,
        shipping,
        distance,
        reason,
        shipping_reason,
        pickup_candidate,
        shipping_candidate,
        precision,
    )
