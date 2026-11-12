"""Loopback source used to verify the collection process with deterministic evidence."""

import json
import re
from datetime import UTC, datetime
from http.client import HTTPConnection, HTTPException
from typing import Literal, cast
from urllib.parse import urlencode, urlsplit

from garimpei.domain.listing.geography import Point
from garimpei.domain.listing.listing import Candidate, Evidence, Match, money
from garimpei.domain.listing.ports import ListingUnavailable, Page, SourceFailure
from garimpei.domain.listing.scope import Scope, Search
from garimpei.infra.gateway.listing.cep_geocoding import verified_point
from garimpei.infra.gateway.listing.external_text import evidence_text
from garimpei.infra.gateway.listing.identity import marketplace_id
from garimpei.infra.gateway.listing.media import https_media


def _mapping(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise SourceFailure("invalid_response")
    return cast(dict[str, object], value)


def _text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _flag(value: object) -> bool | None:
    return value if isinstance(value, bool) else None


def _cep(value: object) -> str | None:
    return value if isinstance(value, str) and re.fullmatch(r"[0-9]{8}", value) else None


def _timestamp(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        stamp = datetime.fromisoformat(value)
    except ValueError:
        return None
    return stamp.astimezone(UTC) if stamp.tzinfo is not None else None


def _candidate(
    raw: object,
    origin: Literal["card", "detail"],
    match: Match | None = None,
) -> Candidate:
    row = _mapping(raw)
    link = _text(row.get("url"))
    identity = marketplace_id(link) if link else None
    if identity is None:
        raise SourceFailure("unverified_identity")
    delivery_cep = _cep(row.get("delivery_cep"))
    raw_publication = row.get("published_at")
    published_at = _timestamp(raw_publication)
    publication_source = None
    if raw_publication is not None:
        publication_source = (
            "fixture.published_at" if published_at is not None else "fixture.published_at.invalid"
        )
    return Candidate(
        identity,
        Evidence(
            image_url=https_media(row.get("image_url")),
            title=evidence_text(row.get("title")),
            description=evidence_text(row.get("description")),
            condition=evidence_text(row.get("condition")),
            published_at=published_at,
            published_at_source=publication_source,
            price=money(_text(row.get("price"))),
            freight=money(_text(row.get("freight"))),
            freight_cep=_cep(row.get("freight_cep")),
            pickup=_flag(row.get("pickup")),
            location=verified_point(row.get("location")),
            delivery=_flag(row.get("delivery")) if delivery_cep else None,
            delivery_cep=delivery_cep,
            shipping_offered=_flag(row.get("shipping_offered")),
            shipping_evidence=evidence_text(row.get("shipping_evidence")),
            pickup_scope_verified=_flag(row.get("pickup_scope_verified")),
            source_available=True if origin == "detail" else None,
        ),
        origin,
        (match,) if match else (),
    )


class FixtureSource:
    def __init__(self, url: str, timeout: int) -> None:
        self._port = urlsplit(url).port
        self._timeout = timeout

    def _get(self, route: str, context: dict[str, str]) -> dict[str, object]:
        connection = HTTPConnection("127.0.0.1", self._port, timeout=self._timeout)
        try:
            connection.request("GET", f"{route}?{urlencode(context)}")
            response = connection.getresponse()
            if response.status != 200:
                raise self._http_failure(response.status, response.getheader("Retry-After", ""))
            payload = response.read(2_000_001)
            if len(payload) > 2_000_000:
                raise SourceFailure("response_too_large")
            return _mapping(json.loads(payload))
        except (OSError, HTTPException):
            raise SourceFailure("source_transport") from None
        except (UnicodeError, ValueError):
            raise SourceFailure("invalid_response") from None
        finally:
            connection.close()

    @staticmethod
    def _http_failure(status: int, retry: str) -> SourceFailure:
        delay = int(retry) if retry.isascii() and retry.isdecimal() and len(retry) < 8 else 0
        if status in (401, 403):
            return SourceFailure("access_denied", delay, access=True)
        if status == 429:
            return SourceFailure("source_rate_limit", delay)
        return SourceFailure(f"source_http_{status}", delay)

    def search(self, scope: Scope, query: Search, continuation: str | None) -> Page:
        context = {
            "kind": query.interest.kind,
            "term": query.term,
            "modality": query.modality,
            "cep": scope.cep,
            "territory": "sao-paulo-sp" if query.modality == "pickup" else "br",
        }
        row = self._get("/search", context | {"page": continuation or ""})
        if row.get("context") != context:
            raise SourceFailure("wrong_search_context")
        raw = row.get("cards")
        next_page = row.get("next")
        if not isinstance(raw, list) or len(raw) > 200:
            raise SourceFailure("invalid_cards")
        if next_page is None and row.get("end") is not True:
            raise SourceFailure("unverified_boundary")
        if next_page is not None and (
            not isinstance(next_page, str)
            or not 1 <= len(next_page) <= 500
            or row.get("end") is not False
        ):
            raise SourceFailure("invalid_continuation")
        if not raw and row.get("empty") is not True:
            raise SourceFailure("unverified_empty")
        candidates: list[Candidate] = []
        invalid = 0
        for card in raw:
            try:
                candidates.append(_candidate(card, "card", query.interest))
            except SourceFailure:
                invalid += 1
        return Page(tuple(candidates), next_page, invalid)

    def detail(self, scope: Scope, external_id: str) -> Candidate:
        row = self._get(f"/detail/{external_id}", {"cep": scope.cep})
        candidate = _candidate(row, "detail")
        if candidate.external_id != external_id or row.get("context_cep") != scope.cep:
            raise SourceFailure("wrong_detail_context")
        if row.get("unavailable") is True:
            raise ListingUnavailable(external_id, "source_unavailable_product")
        return candidate

    def resolve(self, cep: str) -> Point | None:
        row = self._get("/cep", {"cep": cep})
        if row.get("cep") != cep:
            raise SourceFailure("wrong_geocoding_context")
        return verified_point(row.get("point"))
