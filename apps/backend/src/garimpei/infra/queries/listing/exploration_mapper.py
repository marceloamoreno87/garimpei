import json
from dataclasses import asdict
from datetime import datetime
from decimal import Decimal
from typing import cast
from uuid import UUID

from garimpei.domain.listing.condition import ConditionState, automatic_condition
from garimpei.domain.listing.exploration import Offer
from garimpei.domain.listing.listing import Evidence
from garimpei.domain.listing.scope import Modality
from garimpei.domain.valuation.profit import Component, ModalityProfit, ProfitComposition
from garimpei.infra.repository.listing.mapper import EvidenceRecord, decode_evidence
from garimpei.infra.repository.valuation.mapper import (
    decode_valuation,
    encode_valuation,
    mapping,
    records,
)


def encode(offer: Offer) -> dict[str, object]:
    raw = asdict(offer)
    evidence = cast(dict[str, object], raw["evidence"])
    evidence.pop("media", None)
    evidence["image_url"] = None
    raw["valuation"] = (
        encode_valuation(offer.valuation) if offer.valuation and offer.valuation.id else None
    )
    # Calculation time is diagnostic, not changing presentation content.
    composition = cast(dict[str, object], raw["composition"])
    composition.pop("calculated_at")
    raw.pop("condition")
    return cast(dict[str, object], json.loads(json.dumps(raw, default=str)))


def decimal(value: object) -> Decimal | None:
    return Decimal(str(value)) if value is not None else None


def component(raw: object) -> Component:
    row = mapping(raw)
    return Component(
        decimal(row["value"]),
        str(row["state"]),
        str(row["origin"]) if row["origin"] else None,
        str(row["reason"]) if row.get("reason") else None,
    )


def identity(value: object) -> UUID | None:
    return UUID(str(value)) if value else None


def composition(raw: object, at: datetime) -> ProfitComposition:
    row = mapping(raw)
    return ProfitComposition(
        UUID(str(row["listing_id"])),
        UUID(str(row["observation_id"])),
        identity(row["event_id"]),
        identity(row["configuration_id"]),
        int(str(row["configuration_revision"])) if row["configuration_revision"] else None,
        identity(row["evaluation_id"]),
        int(str(row["evaluation_revision"])) if row["evaluation_revision"] else None,
        at,
        component(row["purchase"]),
        component(row["resale"]),
        decimal(row["fee_percent"]),
        component(row["fee"]),
        component(row["shipping_freight"]),
        cast(Modality | None, row["principal"]),
        tuple(
            ModalityProfit(
                cast(Modality, r["modality"]),
                component(r["freight"]),
                component(r["profit"]),
                tuple(cast(list[str], r["reasons"])),
            )
            for r in records(row["modalities"])
        ),
        tuple(cast(list[str], row["reasons"])),
        currency=str(row.get("currency", "BRL")),
        policy=str(row.get("policy", "profit-brl-v1")),
        excluded_costs=tuple(cast(list[str], row.get("excluded_costs", []))),
    )


def missing_composition(
    raw: dict[str, object], evidence: Evidence, at: datetime
) -> ProfitComposition:
    absent = Component(None, "indisponivel", None, "composicao_indisponivel")
    return ProfitComposition(
        UUID(str(raw["id"])),
        UUID(int=0),
        None,
        None,
        None,
        None,
        None,
        at,
        Component(
            evidence.price,
            "conhecido" if evidence.price is not None else "indisponivel",
            "observation",
        ),
        absent,
        None,
        absent,
        absent,
        None,
        (),
        ("composicao_indisponivel",),
    )


def decode(raw: dict[str, object], at: datetime, state: ConditionState | None = None) -> Offer:
    evidence = decode_evidence(cast(EvidenceRecord, raw["evidence"]))
    value = (
        composition(raw["composition"], at)
        if raw.get("composition")
        else missing_composition(raw, evidence, at)
    )
    return Offer(
        UUID(str(raw["id"])),
        str(raw["external_id"]),
        str(raw["source"]),
        str(raw["url"]),
        datetime.fromisoformat(str(raw["first_seen_at"])),
        datetime.fromisoformat(str(raw["observed_at"])),
        evidence,
        state or ConditionState(automatic_condition(evidence)),
        tuple(cast(list[str], raw["categories"])),
        bool(raw["pickup"]),
        bool(raw["shipping"]),
        bool(raw["visible"]),
        value,
        decode_valuation(mapping(raw["valuation"])) if raw["valuation"] else None,
        bool(raw["unavailable"]),
        datetime.fromisoformat(str(raw["last_valid_at"])) if raw["last_valid_at"] else None,
        identity(raw.get("observation_id", value.observation_id)),
        decode_gallery(raw.get("media")),
    )


def decode_gallery(value: object) -> "MediaGallery | None":
    if not value:
        return None
    row = mapping(value)
    return MediaGallery(
        UUID(str(row["listing_id"])),
        UUID(str(row["observation_id"])),
        identity(row.get("capture_id")),
        int(str(row["revision"])),
        str(row["presence"]),
        str(row["state"]),
        str(row["reason"]),
        bool(row["complete"]),
        int(str(row["known_count"])) if row.get("known_count") is not None else None,
        tuple(
            MediaPhoto(
                str(p["key"]),
                int(str(p["position"])),
                bool(p["primary"]),
                identity(p["version_id"]),
                str(p["state"]),
                str(p["thumbnail_state"]),
                str(p["sha256"]),
                str(p["mime"]),
                int(str(p["width"])),
                int(str(p["height"])),
                int(str(p["byte_count"])),
                datetime.fromisoformat(str(p["obtained_at"])) if p.get("obtained_at") else None,
                str(p.get("reason", "")),
            )
            for p in records(row.get("photos", []))
        ),
    )


from garimpei.domain.media.media import MediaGallery, MediaPhoto  # noqa: E402
