import hashlib
import json
import re
from uuid import UUID

from garimpei.config.env import load_inference_settings
from garimpei.domain.inference.condition_evidence import PROMPT, SCHEMA, VERSION
from garimpei.domain.listing.assessment_policy import POLICY_VERSION
from garimpei.domain.listing.assessment_ports import AssessmentError, AssessmentInput
from garimpei.domain.listing.condition import normalized
from garimpei.domain.valuation.identity import identify
from garimpei.infra.gateway.inference.input_preparer import read_lock
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.queries.media.postgres_queries import PostgresMediaQueries
from garimpei.infra.repository.listing.mapper import decode_evidence


class LocalAssessmentInputs:
    def read(self, identity: UUID) -> AssessmentInput:
        listing = Listing.objects.select_related("latest").get(id=identity)
        obs = listing.latest
        if obs is None:
            raise AssessmentError("observation_missing")
        evidence = decode_evidence(obs.evidence)
        text = {key: getattr(evidence, key) for key in ["title", "description", "condition"]}
        category = category_for(evidence.title or "")
        gallery = PostgresMediaQueries().gallery(listing.id, obs.id)
        photos = [
            dict(
                photo_id="p_" + p.sha256,
                sha256=p.sha256,
                version_id=str(p.version_id),
                state=p.state,
                key=p.key,
                position=p.position,
            )
            for p in gallery.photos
        ]
        model = str(read_lock(load_inference_settings().model_lock)["model_digest"])
        semantic = dict(
            listing=str(identity),
            text=text,
            category=category,
            identity=identify(evidence),
            photos=list(dict.fromkeys(str(p["sha256"]) for p in photos)),
            presence=gallery.presence,
            complete=gallery.complete,
            availability=[p["state"] for p in photos],
            model=model,
            policy=POLICY_VERSION,
            prompt=VERSION,
            schema=VERSION,
            prompt_hash=hashlib.sha256(PROMPT.encode()).hexdigest(),
            schema_hash=hashlib.sha256(json.dumps(SCHEMA, sort_keys=True).encode()).hexdigest(),
        )
        fingerprint = hashlib.sha256(json.dumps(semantic, sort_keys=True).encode()).hexdigest()
        snapshot: dict[str, object] = dict(
            text=text,
            category=category,
            identity=identify(evidence),
            photos=photos,
            media_revision=gallery.revision,
            capture_id=str(gallery.capture_id),
            presence=gallery.presence,
            complete=gallery.complete,
            media_state=gallery.state,
        )
        return AssessmentInput(identity, obs.id, obs.ordinal, fingerprint, model, snapshot)


def category_for(title: str) -> str:
    value = normalized(title)
    patterns = [
        ("camera", r"\b(?:camera|canon|nikon)\b"),
        ("computer", r"\b(?:notebook|laptop|computador|macbook)\b"),
        ("console", r"\b(?:playstation|ps5|xbox|nintendo|console)\b"),
        ("headphone", r"\b(?:fone|headphone|headset)\b"),
        ("television", r"\b(?:tv|televisao|televisor)\b"),
        ("electronics", r"\b(?:iphone|celular|smartphone)\b"),
    ]
    matches = [category for category, pattern in patterns if re.search(pattern, value)]
    return matches[0] if len(matches) == 1 else "unknown"
