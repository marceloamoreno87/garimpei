import json
from decimal import Decimal

from garimpei.infra.gateway.listing.relay_parser import (
    JsonObject,
    documents,
    feed_from,
    listing_from,
)


def test_relay_price_identity_condition_and_uncertainty() -> None:
    row: JsonObject = {
        "id": "2044101632968978",
        "marketplace_listing_title": "Vendo Playstation 5 Slim 1tera",
        "listing_price": {"amount": "2300.00", "currency": "BRL"},
        "strikethrough_price": {"amount": "2700.00", "currency": "BRL"},
        "attribute_data": [
            {"attribute_name": "Condição", "value": "used_like_new", "label": "Usado — seminovo"}
        ],
        "redacted_description": {"text": "Console funcionando"},
        "creation_time": 1794347762,
        "delivery_types": ["IN_PERSON"],
        "location_text": {"text": "São Paulo, SP"},
        "location": {"latitude": -23.55, "longitude": -46.63},
        "is_shipping_offered": True,
        "formatted_shipping_price": "R$ 50",
    }
    candidate = listing_from(row, detail=True)
    assert candidate is not None
    evidence = candidate.evidence
    assert evidence.price == Decimal("2300.00")
    assert evidence.condition == "Usado — seminovo"
    assert evidence.description == "Console funcionando" and evidence.pickup
    assert evidence.published_at is not None
    assert evidence.location is not None and evidence.location.accuracy_m is None
    # Generic shipping and a shipping price do not establish delivery at the configured CEP.
    assert evidence.delivery is None and evidence.delivery_cep is None and evidence.freight is None
    foreign = listing_from(
        row | {"listing_price": {"amount": "2300.00", "currency": "USD"}}, detail=False
    )
    assert foreign is not None and foreign.evidence.price is None
    assert listing_from(row | {"id": "malformed/identity"}, detail=True) is None


def test_relay_search_feed_isolated_from_recommendations_and_empty_proof() -> None:
    listing = {
        "id": "101",
        "marketplace_listing_title": "PlayStation 5",
        "listing_price": {"formatted_amount": "R$2.300"},
    }
    body = {
        "data": {
            "marketplace_search": {
                "feed_units": {
                    "edges": [{"node": {"listing": listing}}],
                    "page_info": {"has_next_page": True},
                }
            },
            "recommendations": [{"id": "999", "marketplace_listing_title": "Other item"}],
        },
    }
    result = feed_from(documents(json.dumps(body)))
    assert result is not None and len(result.listings) == 1
    assert result.listings[0]["id"] == "101" and result.has_next
    empty = feed_from(
        documents(
            json.dumps(
                {
                    "data": {
                        "marketplace_search": {
                            "feed_units": {
                                "edges": [],
                                "page_info": {"has_next_page": False},
                            }
                        }
                    },
                }
            )
        )
    )
    assert empty is not None and empty.empty and not empty.has_next
    assert feed_from(documents('{"data":{"something_else":{}}}')) is None


def test_shipping_requires_explicit_offer_and_preserves_source_order() -> None:
    row: JsonObject = {"id": "101", "marketplace_listing_title": "PlayStation 5"}
    for description, offered in (
        ("Envio para todo o Brasil", True),
        ("Envio via correios com rastreio", True),
        ("Não envio para todo Brasil", None),
        ("Frete estimado R$ 50", None),
    ):
        candidate = listing_from(row | {"redacted_description": {"text": description}}, detail=True)
        assert candidate is not None
        assert candidate.evidence.shipping_offered is offered
        assert candidate.evidence.delivery is None
    body = {
        "marketplace_search": {
            "feed_units": {
                "edges": [{"node": {"listing": row}}, {"node": {"listing": row | {"id": "102"}}}],
                "page_info": {"has_next_page": True, "end_cursor": "native-cursor"},
            }
        }
    }
    feed = feed_from(documents(json.dumps(body)))
    assert feed is not None
    assert [item["id"] for item in feed.listings] == ["101", "102"]
    assert feed.cursor == "native-cursor"

    end_node: JsonObject = {"is_main_results_empty": True}
    marker = {
        "marketplace_search": {
            "feed_units": {
                "edges": [
                    {"node": {"listing": row}},
                    {"node": end_node},
                    {"node": {"listing": row | {"id": "999"}}},
                ],
                "page_info": {"has_next_page": True, "end_cursor": "recommendations"},
            }
        }
    }
    main_empty = feed_from(documents(json.dumps(marker)))
    assert main_empty is not None and main_empty.main_results_ended and main_empty.has_next

    assert [item["id"] for item in main_empty.listings] == ["101"]

    end_node.clear()
    end_node.update(
        {"__typename": "MarketplaceSearchFeedEndOfResults", "story_type": "SERP_END_OF_RESULTS"}
    )
    terminal = feed_from(documents(json.dumps(marker)))
    assert terminal is not None and terminal.main_results_ended
    assert [item["id"] for item in terminal.listings] == ["101"]


def test_native_cursor_is_preserved_byte_for_byte_instead_of_trimmed() -> None:
    cursor = ' {"opaque":"value with spaces"} '
    feed = feed_from(
        documents(
            json.dumps(
                {
                    "marketplace_search": {
                        "feed_units": {
                            "edges": [],
                            "page_info": {"has_next_page": True, "end_cursor": cursor},
                        }
                    }
                }
            )
        )
    )
    assert feed is not None and feed.cursor == cursor
