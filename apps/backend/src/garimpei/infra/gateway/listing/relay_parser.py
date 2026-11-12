"""Translate only listing evidence from the JSON rendered by Marketplace pages."""

import json
import re
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import cast

from garimpei.domain.listing.geography import Point
from garimpei.domain.listing.listing import Candidate, Evidence, Match, canonical_url, money
from garimpei.infra.gateway.listing.external_text import evidence_text
from garimpei.infra.gateway.listing.identity import marketplace_id

type JsonValue = None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]
type JsonObject = dict[str, JsonValue]


def objects(value: JsonValue) -> Iterator[JsonObject]:
    pending = [value]
    while pending:
        entry = pending.pop()
        if isinstance(entry, dict):
            yield entry
            pending.extend(reversed(list(entry.values())))
        if isinstance(entry, list):
            pending.extend(reversed(entry))


def mapping(value: JsonValue) -> JsonObject:
    return value if isinstance(value, dict) else {}


def text(value: JsonValue) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def documents(payload: str) -> tuple[JsonObject, ...]:
    result: list[JsonObject] = []
    for line in payload.removeprefix("for (;;);").splitlines():
        try:
            value = cast(JsonValue, json.loads(line))
        except (ValueError, RecursionError):
            continue
        result.extend(objects(value))
    return tuple(result)


@dataclass(frozen=True)
class Feed:
    listings: tuple[JsonObject, ...]
    has_next: bool | None
    empty: bool
    cursor: str | None = None
    main_results_ended: bool = False


def feed_from(rows: tuple[JsonObject, ...]) -> Feed | None:
    for row in rows:
        search = mapping(row.get("marketplace_search"))
        feed = mapping(search.get("feed_units"))
        if feed:
            return _feed(feed)
    return None


def _feed(feed: JsonObject) -> Feed:
    edges = feed.get("edges")
    nodes = tuple(objects(edges)) if isinstance(edges, list) else ()
    listings: list[JsonObject] = []
    empty = False
    for row in nodes:
        if row.get("is_main_results_empty") is True or (
            row.get("__typename") == "MarketplaceSearchFeedEndOfResults"
            and row.get("story_type") == "SERP_END_OF_RESULTS"
        ):
            empty = True
            break
        if "marketplace_listing_title" in row:
            listings.append(row)
    next_page = mapping(feed.get("page_info")).get("has_next_page")
    return Feed(
        tuple(listings),
        next_page if isinstance(next_page, bool) else None,
        empty or edges == [],
        text(mapping(feed.get("page_info")).get("end_cursor")),
        empty,
    )


def route_from(rows: tuple[JsonObject, ...]) -> JsonObject:
    for row in rows:
        info = mapping(row.get("initialRouteInfo"))
        route = mapping(info.get("route"))
        params = mapping(route.get("params"))
        if "query" in params or "category_id" in params:
            return route
    return {}


def listing_from(row: JsonObject, *, detail: bool, match: Match | None = None) -> Candidate | None:
    external_id = text(row.get("id"))
    if external_id is None or marketplace_id(canonical_url(external_id)) != external_id:
        return None
    delivery = row.get("delivery_types")
    pickup = None
    if isinstance(delivery, list) and delivery:
        pickup = bool(
            {"IN_PERSON", "PUBLIC_MEETUP"} & set(x for x in delivery if isinstance(x, str))
        )
    location = _location(row)
    from garimpei.infra.gateway.listing.media import https_media
    from garimpei.infra.gateway.media.gallery_parser import extract_gallery

    evidence = Evidence(
        media=extract_gallery(row, detail),
        image_url=https_media(mapping(row.get("primary_listing_photo")).get("image_uri")),
        title=evidence_text(row.get("marketplace_listing_title")),
        description=evidence_text(mapping(row.get("redacted_description")).get("text")),
        condition=evidence_text(_condition(row)),
        published_at=_published(row.get("creation_time")),
        published_at_source=(
            "facebook.creation_time"
            if _published(row.get("creation_time"))
            else "facebook.creation_time.invalid"
            if row.get("creation_time") is not None
            else None
        ),
        price=_price(row),
        pickup=pickup,
        location=location,
        shipping_offered=_shipping_offered(row),
        shipping_evidence=_shipping_evidence(row),
        source_available=True if detail else None,
    )
    return Candidate(
        external_id, evidence, "detail" if detail else "card", (match,) if match else ()
    )


def _price(row: JsonObject) -> Decimal | None:
    price = mapping(row.get("listing_price"))
    if price.get("currency") not in (None, "BRL"):
        return None
    # Ignore strikethrough prices, installments and prices for unrelated recommendations.
    label = text(price.get("formatted_amount")) or text(
        price.get("formatted_amount_zeros_stripped")
    )
    amount = price.get("amount")
    if price.get("currency") != "BRL":
        return money(label)
    try:
        value = Decimal(amount) if isinstance(amount, str) else None
    except InvalidOperation:
        return None
    if value is None or not value.is_finite() or not 0 <= value < Decimal("1000000000000"):
        return None
    if value != value.quantize(Decimal("0.01")):
        return None
    return value


def _published(value: JsonValue) -> datetime | None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    try:
        return datetime.fromtimestamp(value, UTC) if value > 0 else None
    except (ValueError, OverflowError, OSError):
        return None


def _location(row: JsonObject) -> Point | None:
    location = mapping(row.get("location")) or mapping(row.get("item_location"))
    reverse = mapping(location.get("reverse_geocode"))
    city = evidence_text(reverse.get("city"))
    state = evidence_text(reverse.get("state"))
    label = evidence_text(mapping(row.get("location_text")).get("text"))
    if label and "," in label:
        city, state = (piece.strip() for piece in label.rsplit(",", 1))
    if not city or not state:
        return None
    latitude, longitude = location.get("latitude"), location.get("longitude")
    if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
        # A city proves municipality but cannot prove listing coordinates.
        return Point(0, 0, None, city, state, coordinates_known=False)
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        return None
    # Marketplace labels these positions approximate without an error radius.
    return Point(float(latitude), float(longitude), None, city, state)


def _condition(row: JsonObject) -> str | None:
    data = row.get("attribute_data")
    for attribute in objects(data):
        label = text(attribute.get("attribute_name")) or text(attribute.get("label"))
        if label and label.casefold() in {"condition", "condição"}:
            return (
                text(attribute.get("label"))
                or text(attribute.get("value"))
                or text(attribute.get("attribute_value"))
            )
    return None


def _shipping_evidence(row: JsonObject) -> str | None:
    delivery = row.get("delivery_types")
    if row.get("is_shipping_offered") is True or row.get("shipping_offered") is True:
        return "source_shipping_offered"
    if isinstance(delivery, list) and "SHIPPING" in delivery:
        return "source_delivery_types"
    description = text(mapping(row.get("redacted_description")).get("text")) or ""
    if re.search(
        r"\b(envio|enviamos|envia|envios)\s+(para\s+)?(todo\s+(o\s+)?brasil|via\s+(correios|transportadora))",
        description,
        re.IGNORECASE,
    ):
        if not re.search(r"\bn[aã]o\s+(envio|enviamos|envia)", description, re.IGNORECASE):
            return "listing_description_shipping"
    return None


def _shipping_offered(row: JsonObject) -> bool | None:
    if _shipping_evidence(row) is not None:
        return True
    value = row.get("is_shipping_offered")
    return value if isinstance(value, bool) else None


def browse_parameters(rows: tuple[JsonObject, ...]) -> JsonObject:
    for row in rows:
        variables = mapping(row.get("variables"))
        params = variables.get("params")
        if isinstance(params, str):
            params = next(iter(documents(params)), {})
        browse = mapping(mapping(params).get("browse_request_params"))
        if browse:
            return browse
    return {}
