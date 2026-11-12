import json
from dataclasses import replace
from datetime import datetime
from uuid import UUID, uuid4

from django.db import transaction

from garimpei.domain.inference.condition_evidence import VERSION
from garimpei.domain.listing.assessment import Assessment
from garimpei.domain.listing.assessment_policy import POLICY_VERSION
from garimpei.domain.listing.assessment_ports import (
    AssessmentError,
    AssessmentInput,
    AssessmentWork,
)
from garimpei.infra.persistence.assessment_models import AssessmentHead, ConditionAssessment
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.persistence.media_models import MediaCapture
from garimpei.infra.persistence.monitoring_unit_of_work import lock_monitoring_publication
from garimpei.infra.queries.listing.assessment_validity import applicable, model_revision
from garimpei.infra.queries.media.postgres_queries import PostgresMediaQueries
from garimpei.infra.repository.listing.assessment_mapper import (
    encode_assessment,
    work_from_row,
)


class PostgresAssessmentRepository:
    def prepare(self, value: AssessmentInput, now: datetime) -> AssessmentWork:
        with transaction.atomic():
            listing = Listing.objects.select_for_update().get(id=value.listing_id)
            if listing.latest_id != value.observation_id:
                raise AssessmentError("superseded_input")
            head, created = AssessmentHead.objects.get_or_create(
                listing=listing,
                defaults=dict(
                    observation_id=value.observation_id,
                    input_fingerprint=value.fingerprint,
                    updated_at=now,
                ),
            )
            if (
                head.current_id
                and head.observation_id == value.observation_id
                and head.input_fingerprint == value.fingerprint
            ):
                head.updated_at = now
                head.save(update_fields=["updated_at"])
                return work_from_row(
                    ConditionAssessment.objects.select_related("observation").get(
                        id=head.current_id
                    )
                )
            if not created:
                head.generation += 1
            head.observation_id = value.observation_id
            head.input_fingerprint = value.fingerprint
            row, _ = ConditionAssessment.objects.get_or_create(
                listing=listing,
                observation_id=value.observation_id,
                input_fingerprint=value.fingerprint,
                defaults=dict(
                    id=uuid4(),
                    policy_version=POLICY_VERSION,
                    prompt_version=VERSION,
                    schema_version=VERSION,
                    model_revision=value.model_revision,
                    input_snapshot=value.snapshot,
                    generation=head.generation,
                    created_at=now,
                    updated_at=now,
                ),
            )
            if row.publication_order is None and row.generation != head.generation:
                row.generation = head.generation
                row.save(update_fields=["generation"])
            cached = (
                ConditionAssessment.objects.filter(
                    listing=listing, input_fingerprint=value.fingerprint, status="complete"
                )
                .exclude(id=row.id)
                .order_by("-analyzed_at")
                .first()
            )
            if cached and row.result is None:
                row.result = cached.result
                row.reason = "cached_result"
                row.inference_refs = cached.inference_refs
                row.save()
            head.current = row
            head.updated_at = now
            head.save()
            return work_from_row(row)

    def work(self, identity: UUID) -> AssessmentWork:
        return work_from_row(
            ConditionAssessment.objects.select_related("observation").get(id=identity)
        )

    def attach(
        self,
        work: AssessmentWork,
        requests: tuple[UUID, ...],
        pins: tuple[UUID, ...],
        now: datetime,
    ) -> None:
        with transaction.atomic():
            row = ConditionAssessment.objects.select_for_update().get(id=work.id)
            if row.inference_refs and row.inference_refs != [str(r) for r in requests]:
                raise AssessmentError("request_conflict")
            row.inference_refs = [str(r) for r in requests]
            row.media_references = [str(r) for r in pins]
            row.updated_at = now
            row.save()

    def publish(self, work: AssessmentWork, value: Assessment, now: datetime) -> bool:
        with transaction.atomic():
            lock_monitoring_publication()
            listing = Listing.objects.select_for_update().get(id=work.value.listing_id)
            head = AssessmentHead.objects.select_for_update().get(listing=listing)
            row = ConditionAssessment.objects.select_for_update().get(id=work.id)
            if row.publication_order is not None:
                return False
            current = (
                listing.latest_id == row.observation_id
                and head.current_id == row.id
                and head.generation == work.generation
            )
            current = current and head.input_fingerprint == work.value.fingerprint
            MediaCapture.objects.select_for_update().filter(
                observation_id=row.observation_id
            ).first()
            current = current and applicable(
                row,
                PostgresMediaQueries().gallery(row.listing_id, row.observation_id),
                model_revision(),
            )
            if not current:
                row.status = "superseded"
                row.reason = "superseded_input"
                row.result = json.loads(json.dumps(encode_assessment(value), default=str))
                row.save()
                return False
            listing.publication_order += 1
            listing.save(update_fields=["publication_order"])
            value = replace(
                value,
                id=row.id,
                observation_id=row.observation_id,
                fingerprint=row.input_fingerprint,
                model_revision=row.model_revision,
                previous=head.confirmed_id,
                revision=work.generation,
            )
            row.status = value.status
            row.condition = value.condition
            row.sufficient = value.sufficient
            row.reason = value.reason
            row.analyzed_at = value.analyzed_at
            row.updated_at = now
            row.result = json.loads(json.dumps(encode_assessment(value), default=str))
            row.publication_order = listing.publication_order
            row.save()
            if value.status == "complete":
                head.confirmed = row
            head.updated_at = now
            head.save()
            # The existing repair/publisher consumes this changed publication order.
            from garimpei.infra.repository.alert.first_inputs import invalidate_first_alert

            invalidate_first_alert(listing.id, now)
            return True
