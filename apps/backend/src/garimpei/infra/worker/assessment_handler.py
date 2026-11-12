import logging
from uuid import UUID

from django.db.models import F
from django.utils.timezone import now

from garimpei.domain.inference.errors import InferenceError
from garimpei.domain.listing.assessment import Assessment
from garimpei.domain.listing.assessment_ports import AssessmentError
from garimpei.domain.media.errors import MediaError
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.repository.listing.assessment_repository import PostgresAssessmentRepository
from garimpei.usecase.listing.complete_assessment_usecase import CompleteAssessmentUseCase
from garimpei.usecase.listing.prepare_assessment_usecase import PrepareAssessmentUseCase

logger = logging.getLogger(__name__)


class AssessmentHandler:
    def __init__(
        self,
        prepare: PrepareAssessmentUseCase,
        complete: CompleteAssessmentUseCase,
        repository: PostgresAssessmentRepository,
    ) -> None:
        self._prepare, self._complete, self._repository = prepare, complete, repository

    def execute(self) -> None:
        # Rotating by update time gives bounded adoption and progress for new stock.
        rows = (
            Listing.objects.exclude(latest=None)
            .order_by(F("assessment_head__updated_at").asc(nulls_first=True), "id")
            .values_list("id", flat=True)[:10]
        )
        for identity in rows:
            self._one(identity)

    def _one(self, identity: UUID) -> None:
        try:
            work = self._prepare.execute(identity)
            self._complete.execute(work.id)
        except (InferenceError, MediaError, AssessmentError) as error:
            logger.info(
                "condition_assessment_waiting",
                extra=dict(
                    event="condition_assessment_waiting",
                    listing_id=str(identity),
                    error_code=error.code,
                ),
            )
            # Failed preparation is represented conservatively; no inference/attempt counters are duplicated.
            from garimpei.infra.persistence.assessment_models import AssessmentHead

            head = AssessmentHead.objects.filter(listing_id=identity).first()
            if head and head.current_id:
                current = self._repository.work(head.current_id)
                self._repository.publish(
                    current,
                    Assessment(
                        status="failed",
                        reason="invalid_analysis"
                        if error.code == "invalid_output"
                        else "model_unavailable",
                    ),
                    now(),
                )
