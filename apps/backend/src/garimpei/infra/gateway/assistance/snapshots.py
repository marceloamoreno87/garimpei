"""Only deterministic, catalog-backed facts enter the model's finite choice set."""

import hashlib
import json
from dataclasses import asdict
from typing import cast
from uuid import UUID

from garimpei.config.env import load_inference_settings
from garimpei.domain.assistance.review import POLICY, PROFILES, assistance_prompt, assistance_schema
from garimpei.domain.valuation.identification_values import IdentificationResult, IdentityAttribute
from garimpei.domain.valuation.policy import eligible
from garimpei.domain.valuation.product_catalog import REQUIRED
from garimpei.infra.gateway.inference.input_preparer import artifact_signature, read_lock
from garimpei.infra.persistence.assistance_models import AssistanceOperationsSnapshot
from garimpei.infra.persistence.listing_models import Listing, ListingObservation
from garimpei.infra.persistence.media_models import MediaEntry
from garimpei.infra.persistence.monitoring_models import MonitoringConfiguration, MonitoringInterest
from garimpei.infra.repository.valuation.identity_mapper import identify_row
from garimpei.infra.repository.valuation.mapper import listing_comparable


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def observation_snapshot(
    row: Listing, purpose: str, candidate: ListingObservation | None = None
) -> dict[str, object]:
    assert row.latest is not None
    progress = getattr(row, "identity_progress", None)
    identity = identify_row(row, progress)
    automatic_identity = identify_row(row, None)
    texts = {
        k: str(row.latest.evidence.get(k) or "") for k in ("title", "description", "condition")
    }
    facts: list[dict[str, object]] = []
    for index, attribute in enumerate(automatic_identity.attributes):
        fact = _attribute_fact(index, attribute, texts)
        if fact is not None:
            facts.append(fact)
    values: dict[str, list[str]] = {}
    for fact in facts:
        values.setdefault(str(fact["field"]), []).append(str(fact["value"]))
    snapshot: dict[str, object] = dict(
        policy=POLICY,
        purpose=purpose,
        observation_id=str(row.latest.id),
        revision=row.latest.ordinal,
        manual_revision=identity.manual_revision,
        identity_policy=identity.policy_version,
        texts=texts,
        facts=facts,
        allowed_values=values,
        required_fields=list(REQUIRED.get(identity.family or "", tuple(values))),
        conflict=bool(identity.conflicts),
        identity=_identity_context(identity),
        source_identity=dict(
            state=automatic_identity.state,
            product_key=automatic_identity.product_key,
            missing=list(automatic_identity.missing_attributes),
        ),
        observation_evidence_sha256=digest(row.latest.evidence),
        input_projection="texts-and-catalog-facts-v1",
        unforwarded_fields=[
            "null metadata",
            "duplicate attribute provenance retained by observation",
        ],
        media=_media_snapshot(row.latest.id),
        media_examined=False,
    )
    if purpose == "comparables" and candidate is not None:
        _comparable_facts(snapshot, row, candidate)
    return _profile_context(snapshot, purpose)


def _comparable_facts(
    snapshot: dict[str, object], target: Listing, candidate: ListingObservation
) -> None:
    from django.utils.timezone import now

    row = candidate.listing
    identity = identify_row(row, getattr(row, "identity_progress", None))
    target_identity = identify_row(target, getattr(target, "identity_progress", None))
    key = target_identity.product_key
    comparable = listing_comparable(row, identity)
    same = bool(key and identity.product_key == key and eligible(comparable, key, now()))
    from garimpei.domain.listing.condition import automatic_condition, normalized
    from garimpei.domain.valuation.offer_quality import installment_price

    texts = {
        "candidate_" + k: str(candidate.evidence.get(k) or "")
        for k in ("title", "description", "condition")
    }
    candidate_text = texts["candidate_title"] + " " + texts["candidate_description"]
    evidence = comparable.evidence
    partial = (
        installment_price(normalized(candidate_text), comparable.price)
        if comparable.price is not None
        else False
    )
    accessory = identity.state == "excluded_item" or any(
        term in normalized(candidate_text)
        for term in ("somente controle", "controle avulso", "somente pecas", "para pecas")
    )
    defect = automatic_condition(evidence).condition
    fields = dict(
        equivalence="equivalent" if same else "excluded",
        price_kind="partial"
        if partial
        else "full"
        if comparable.price and comparable.price > 0
        else "unknown",
        accessory="present" if accessory else "none_detected",
        defect="present"
        if defect == "defect"
        else "none_detected"
        if defect == "good"
        else "unknown",
    )
    facts = [
        dict(
            id="candidate-" + field,
            field=field,
            value=value,
            source="deterministic_policy",
        )
        for field, value in fields.items()
    ]
    original = cast(dict[str, object], snapshot.get("texts", {}))
    snapshot.update(
        candidate_observation_id=str(candidate.id),
        candidate_revision=candidate.ordinal,
        candidate_manual_revision=identity.manual_revision,
        texts=original | texts,
        candidate_identity=_identity_context(identity),
        candidate_evidence_sha256=digest(candidate.evidence),
        candidate_source_policy="exact-electronics-v2",
        facts=facts,
        allowed_values={k: [v] for k, v in fields.items()},
        required_fields=list(fields),
        conflict=not same,
        confirmation_allowed=same
        and fields["price_kind"] == "full"
        and fields["accessory"] == "none_detected"
        and fields["defect"] == "none_detected",
    )


def interest_snapshot(row: MonitoringInterest) -> dict[str, object]:
    # Labels are established, user-selected catalog aliases. No generated search term is admitted.
    terms = [row.label] if row.kind == "product" and row.label.strip() else []
    facts = [
        dict(id=f"alias-{i}", field="term", value=term, source="validated_interest")
        for i, term in enumerate(terms)
    ]
    return _profile_context(
        dict(
            policy=POLICY,
            purpose="investigation",
            interest_id=str(row.id),
            revision=row.configuration.revision,
            configuration_id=str(row.configuration_id),
            region_cep=row.configuration.cep,
            facts=facts,
            allowed_values={"term": terms},
            required_fields=["term"],
            conflict=False,
        ),
        "investigation",
    )


def operations_snapshot(row: AssistanceOperationsSnapshot) -> dict[str, object]:
    return _profile_context(
        dict(
            policy=POLICY,
            purpose="operations",
            snapshot_id=str(row.id),
            revision=row.revision,
            content_hash=row.content_hash,
            facts=row.facts,
            allowed_values={
                "action": sorted(
                    {str(f["value"]) for f in cast(list[dict[str, object]], row.facts)}
                )
            },
            required_fields=["action"],
            conflict=False,
        ),
        "operations",
    )


def _attribute_fact(
    index: int, attribute: IdentityAttribute, texts: dict[str, str]
) -> dict[str, object] | None:
    if attribute.origin != "automatic" or not attribute.quote or not attribute.field:
        return None
    source = texts.get(attribute.field, "")
    start = source.find(attribute.quote)
    if start < 0:
        return None
    return dict(
        id=f"attribute-{index}",
        field=attribute.name,
        value=attribute.value,
        source="text",
        text_field=attribute.field,
        start=start,
        end=start + len(attribute.quote),
        quote=attribute.quote,
    )


def _media_snapshot(identity: UUID) -> list[dict[str, object]]:
    return [
        dict(
            id=str(entry.id),
            revision=entry.generation,
            sha256=entry.asset.sha256 if entry.asset else None,
            state=entry.asset.state if entry.asset else "unavailable",
        )
        for entry in MediaEntry.objects.filter(capture__observation_id=identity)
        .select_related("asset")
        .order_by("position")
    ]


def _profile_context(snapshot: dict[str, object], purpose: str) -> dict[str, object]:
    configuration = (
        MonitoringConfiguration.objects.filter(slot="active").values("id", "revision").first()
    )
    snapshot["configuration_revision"] = (
        dict(id=str(configuration["id"]), revision=configuration["revision"])
        if configuration
        else None
    )
    snapshot["model_artifact"] = artifact_signature(read_lock(load_inference_settings().model_lock))
    if purpose in PROFILES:
        profile = PROFILES[purpose]
        snapshot["profile_signature"] = digest(
            dict(
                profile=profile,
                prompt=assistance_prompt(profile),
                schema=assistance_schema(profile, json.dumps(snapshot, default=str)),
            )
        )
    return snapshot


def _identity_context(identity: IdentificationResult) -> dict[str, object]:
    return dict(
        state=identity.state,
        family=identity.family,
        product_key=identity.product_key,
        manual_revision=identity.manual_revision,
        manual_values={
            attribute.name: attribute.value
            for attribute in identity.attributes
            if attribute.origin == "manual"
        },
        conflicts=[asdict(conflict) for conflict in identity.conflicts],
    )
