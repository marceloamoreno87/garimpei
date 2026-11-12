from dataclasses import asdict, replace
from datetime import datetime
from typing import Literal, cast
from uuid import UUID

from garimpei.domain.valuation.identification import identify_product
from garimpei.domain.valuation.identification_values import (
    AttributeConflict,
    IdentificationResult,
    IdentityAttribute,
    IdentityState,
)
from garimpei.domain.valuation.manual_identity import ManualIdentity
from garimpei.infra.persistence.identity_models import IdentityProgress
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.repository.listing.mapper import decode_evidence


def manual_value(progress: IdentityProgress | None) -> ManualIdentity | None:
    if progress is None or progress.manual is None or not progress.manual.values:
        return None
    row = progress.manual
    return ManualIdentity(
        tuple(sorted((str(k), str(v)) for k, v in row.values.items())),
        row.revision,
        row.observation.ordinal,
        row.recorded_at,
        tuple(str(x) for x in row.reviewed_conflicts),
        row.observation_id,
    )


def identify_row(row: Listing, progress: IdentityProgress | None = None) -> IdentificationResult:
    observation = row.latest
    assert observation is not None
    result = identify_product(
        decode_evidence(observation.evidence),
        observation.id,
        observation.ordinal,
        manual_value(progress),
    )
    return replace(result, manual_revision=progress.manual_revision if progress else 0)


def encode_identity(value: IdentificationResult) -> dict[str, object]:
    return dict(
        state=value.state,
        observation_id=str(value.observation_id),
        input_revision=value.input_revision,
        family=value.family,
        product_key=value.product_key,
        attributes=[
            {
                **asdict(a),
                "observation_id": str(a.observation_id),
                "recorded_at": a.recorded_at.isoformat() if a.recorded_at else None,
            }
            for a in value.attributes
        ],
        missing_attributes=list(value.missing_attributes),
        conflicts=[asdict(c) for c in value.conflicts],
        manual_revision=value.manual_revision,
        policy_version=value.policy_version,
    )


def decode_identity(raw: dict[str, object]) -> IdentificationResult:
    attributes = []
    for item in cast(list[dict[str, object]], raw.get("attributes", [])):
        attributes.append(
            IdentityAttribute(
                str(item["name"]),
                str(item["value"]),
                cast(Literal["automatic", "manual"], item["origin"]),
                UUID(str(item["observation_id"])),
                int(str(item["input_revision"])),
                cast("str | None", item.get("field")),
                cast("str | None", item.get("quote")),
                datetime.fromisoformat(str(item["recorded_at"]))
                if item.get("recorded_at")
                else None,
                int(str(item["reviewed_revision"]))
                if item.get("reviewed_revision") is not None
                else None,
                bool(item.get("explicit", True)),
            )
        )
    conflicts = tuple(
        AttributeConflict(
            str(c["name"]),
            cast("str | None", c.get("manual_value")),
            str(c["observed_value"]),
            cast("str | None", c.get("field")),
            cast("str | None", c.get("quote")),
        )
        for c in cast(list[dict[str, object]], raw.get("conflicts", []))
    )
    return IdentificationResult(
        cast(IdentityState, raw["state"]),
        UUID(str(raw["observation_id"])),
        int(str(raw["input_revision"])),
        cast("str | None", raw.get("family")),
        cast("str | None", raw.get("product_key")),
        tuple(attributes),
        tuple(str(x) for x in cast(list[str], raw.get("missing_attributes", []))),
        conflicts,
        int(str(raw.get("manual_revision", 0))),
        str(raw["policy_version"]),
    )


def current_identification(row: Listing) -> IdentificationResult:
    progress = (
        IdentityProgress.objects.select_related("manual__observation").filter(listing=row).first()
    )
    return identify_row(row, progress)
