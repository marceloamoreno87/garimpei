import json
import re
from math import isfinite
from typing import cast
from urllib.request import Request, urlopen

from garimpei.domain.listing.geography import Point
from garimpei.domain.listing.ports import SourceFailure


def _number(value: object) -> float | None:
    if isinstance(value, (float, int)) and not isinstance(value, bool) and isfinite(value):
        return float(value)
    return None


def verified_point(value: object) -> Point | None:
    if not isinstance(value, dict):
        return None
    row = cast(dict[str, object], value)
    latitude, longitude = _number(row.get("latitude")), _number(row.get("longitude"))
    accuracy = _number(row.get("accuracy_m"))
    city, state = row.get("city"), row.get("state")
    if (
        latitude is None
        or not -90 <= latitude <= 90
        or longitude is None
        or not -180 <= longitude <= 180
        or not isinstance(city, str)
        or not isinstance(state, str)
    ):
        return None
    return Point(
        latitude,
        longitude,
        accuracy if accuracy is not None and accuracy >= 0 else None,
        city,
        state,
    )


class BrasilApiGeocoding:
    def __init__(self, timeout: int) -> None:
        self._timeout = timeout
        self._cache: dict[str, Point | None] = {}

    def resolve(self, cep: str) -> Point | None:
        if cep not in self._cache:
            self._cache[cep] = self._lookup(cep)
        return self._cache[cep]

    def _lookup(self, cep: str) -> Point | None:
        if not re.fullmatch(r"[0-9]{8}", cep):
            raise SourceFailure("invalid_cep")
        try:
            with urlopen(
                Request(
                    f"https://brasilapi.com.br/api/cep/v2/{cep}",
                    headers={"Accept": "application/json", "User-Agent": "Garimpei/0.1"},
                ),
                timeout=self._timeout,
            ) as response:
                data = json.loads(response.read(100_000))
        except (OSError, ValueError):
            raise SourceFailure("geocoding_unavailable") from None
        if not isinstance(data, dict) or str(data.get("cep", "")).replace("-", "") != cep:
            raise SourceFailure("geocoding_context_unverified")
        coordinates = data.get("location", {}).get("coordinates", {})
        try:
            latitude, longitude = float(coordinates["latitude"]), float(coordinates["longitude"])
        except (KeyError, TypeError, ValueError):
            raise SourceFailure("geocoding_coordinates_unavailable") from None
        # CEP coordinates supplied by this provider have no published per-result error radius.
        return verified_point(
            {
                "latitude": latitude,
                "longitude": longitude,
                "accuracy_m": None,
                "city": data.get("city"),
                "state": data.get("state"),
            }
        )
