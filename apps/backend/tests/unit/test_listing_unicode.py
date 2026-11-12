import pytest

from garimpei.infra.gateway.listing.media import https_media
from garimpei.infra.gateway.listing.relay_parser import JsonObject, listing_from


@pytest.mark.parametrize("invalid", ["\x00", "\ud800", "\udfff"])
def test_listing_text_replaces_unrepresentable_characters_without_changing_identity(
    invalid: str,
) -> None:
    row: JsonObject = {
        "id": "601",
        "marketplace_listing_title": f"Câmera{invalid}Canon 📷",
        "redacted_description": {"text": f"Funciona{invalid}bem; literal \\u0000"},
        "attribute_data": [{"attribute_name": "condition", "label": f"Usada{invalid}boa"}],
        "location_text": {"text": f"São{invalid}Paulo, SP"},
        "listing_price": {"amount": "1000.00", "currency": "BRL"},
    }
    candidate = listing_from(row, detail=True)
    assert candidate is not None and candidate.external_id == "601"
    assert candidate.evidence.title == "Câmera�Canon 📷"
    assert candidate.evidence.description == "Funciona�bem; literal \\u0000"
    assert candidate.evidence.condition == "Usada�boa"
    assert candidate.evidence.location is not None
    assert candidate.evidence.location.city == "São�Paulo"
    assert listing_from(row | {"id": f"60{invalid}1"}, detail=True) is None
    assert https_media(f"https://example.org/photo{invalid}.jpg") is None


def test_valid_unicode_and_media_are_preserved() -> None:
    row: JsonObject = {
        "id": "601",
        "marketplace_listing_title": "Câmera Canon 📷",
        "redacted_description": {"text": "Descrição íntegra — não apagar"},
    }
    candidate = listing_from(row, detail=True)
    assert candidate is not None
    assert candidate.evidence.title == "Câmera Canon 📷"
    assert candidate.evidence.description == "Descrição íntegra — não apagar"
    assert https_media("https://example.org/câmera.jpg") == "https://example.org/câmera.jpg"
