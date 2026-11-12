from typing import cast
from uuid import UUID

from garimpei.domain.listing.assessment import Assessment
from garimpei.domain.media.media import MediaGallery
from garimpei.infra.persistence.assessment_models import AssessmentHead, ConditionAssessment
from garimpei.infra.queries.listing.assessment_validity import applicable, model_revision
from garimpei.infra.queries.media.postgres_queries import PostgresMediaQueries
from garimpei.infra.repository.listing.assessment_mapper import decode_assessment


class PostgresAssessmentQueries:
    def observation(self, listing_id: UUID, observation_id: UUID) -> Assessment:
        row = (
            ConditionAssessment.objects.filter(listing_id=listing_id, observation_id=observation_id)
            .select_related("listing__latest")
            .order_by("-generation", "-created_at")
            .first()
        )
        if row and row.observation_id == row.listing.latest_id:
            gallery = PostgresMediaQueries().gallery(listing_id, observation_id)
            if not applicable(row, gallery, model_revision()):
                return Assessment(
                    observation_id=observation_id, previous=row.id, reason="superseded_input"
                )
        head = AssessmentHead.objects.filter(listing_id=listing_id).first()
        return assessment_from_row(row, observation_id, head.confirmed_id if head else None)

    def current_many(
        self, identities: tuple[UUID, ...], galleries: dict[UUID, MediaGallery] | None = None
    ) -> dict[UUID, Assessment]:
        heads = list(
            AssessmentHead.objects.filter(listing_id__in=identities).select_related(
                "current__listing__latest"
            )
        )
        if galleries is None:
            galleries = PostgresMediaQueries().galleries(
                tuple((h.listing_id, h.observation_id) for h in heads)
            )
        model = model_revision()
        return {head.listing_id: _current(head, galleries, model) for head in heads}


def _current(head: AssessmentHead, galleries: dict[UUID, MediaGallery], model: str) -> Assessment:
    row = head.current
    gallery = galleries.get(head.observation_id)
    if row and gallery and not applicable(row, gallery, model):
        return Assessment(
            observation_id=head.observation_id,
            previous=head.confirmed_id,
            reason="superseded_input",
        )
    return assessment_from_row(row, head.observation_id, head.confirmed_id)


def assessment_from_row(
    row: ConditionAssessment | None, observation_id: UUID, previous: UUID | None = None
) -> Assessment:
    if row is None:
        return Assessment(observation_id=observation_id, previous=previous)
    if row.result and row.publication_order is not None:
        return decode_assessment(row.result)
    return Assessment(
        id=row.id,
        observation_id=row.observation_id,
        fingerprint=row.input_fingerprint,
        policy_version=row.policy_version,
        status="waiting",
        reason="waiting_inference",
        model_revision=row.model_revision,
        previous=previous,
        photo_coverage=tuple(
            dict(p, examined=False, reason="waiting_inference")
            for p in cast(list[dict[str, object]], row.input_snapshot.get("photos", []))
        ),
    )
