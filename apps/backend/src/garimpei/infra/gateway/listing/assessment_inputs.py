import hashlib
import json
from uuid import UUID

from garimpei.config.env import load_inference_settings
from garimpei.domain.inference.condition_evidence import PROMPT, SCHEMA, VERSION
from garimpei.domain.listing.assessment_policy import POLICY_VERSION
from garimpei.domain.listing.assessment_ports import AssessmentError, AssessmentInput
from garimpei.infra.gateway.inference.input_preparer import read_lock
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.queries.listing.assessment_context import assessment_context
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
        context = assessment_context(listing)
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
            **context,
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
            **context,
            photos=photos,
            media_revision=gallery.revision,
            capture_id=str(gallery.capture_id),
            presence=gallery.presence,
            complete=gallery.complete,
            media_state=gallery.state,
        )
        return AssessmentInput(identity, obs.id, obs.ordinal, fingerprint, model, snapshot)
