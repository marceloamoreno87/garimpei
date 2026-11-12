import uuid

from django.db import models
from django.utils import timezone

from garimpei.infra.persistence.inference_models import InferenceControl as InferenceControl
from garimpei.infra.persistence.inference_models import InferencePart as InferencePart
from garimpei.infra.persistence.inference_models import InferenceRequest as InferenceRequest
from garimpei.infra.persistence.listing_models import CollectionCandidate as CollectionCandidate
from garimpei.infra.persistence.listing_models import CollectionCycle as CollectionCycle
from garimpei.infra.persistence.listing_models import CollectionState as CollectionState
from garimpei.infra.persistence.listing_models import Listing as Listing
from garimpei.infra.persistence.listing_models import ListingEvent as ListingEvent
from garimpei.infra.persistence.listing_models import ListingInterestMatch as ListingInterestMatch
from garimpei.infra.persistence.listing_models import ListingObservation as ListingObservation
from garimpei.infra.persistence.listing_models import ManualCondition as ManualCondition
from garimpei.infra.persistence.monitoring_models import (
    MonitoringConfiguration as MonitoringConfiguration,
)
from garimpei.infra.persistence.monitoring_models import (
    MonitoringInterest as MonitoringInterest,
)
from garimpei.infra.persistence.navigation_models import (
    NavigationCheckpoint as NavigationCheckpoint,
)
from garimpei.infra.persistence.navigation_models import (
    NavigationUnitReceipt as NavigationUnitReceipt,
)
from garimpei.infra.persistence.navigation_models import NavigationWork as NavigationWork
from garimpei.infra.persistence.navigation_models import NicheSuggestion as NicheSuggestion
from garimpei.infra.persistence.navigation_models import SuggestionEvidence as SuggestionEvidence

# Explicit Django model discovery; consumers import the concrete feature module.
from garimpei.infra.persistence.valuation_models import ValuationEvaluation as ValuationEvaluation
from garimpei.infra.persistence.valuation_models import ValuationProgress as ValuationProgress
from garimpei.infra.persistence.valuation_models import ValuationWork as ValuationWork


class RuntimeState(models.Model):
    environment_id = models.CharField(primary_key=True, max_length=64)
    run_id = models.UUIDField()
    started_at = models.DateTimeField(default=timezone.now)
    stopped_at = models.DateTimeField(null=True)
    last_probe_at = models.DateTimeField(null=True)
    probe_sequence = models.PositiveBigIntegerField(default=0)


class RuntimeProbe(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    environment_id = models.CharField(max_length=64)
    run_id = models.UUIDField()
    kind = models.CharField(max_length=10, choices=[("control", "control"), ("manual", "manual")])
    sequence = models.PositiveBigIntegerField()
    created_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["environment_id", "run_id", "kind", "sequence"], name="unique_runtime_probe"
            )
        ]
        indexes = [
            models.Index(
                fields=["environment_id", "run_id", "completed_at"], name="runtime_probe_lookup"
            )
        ]


from garimpei.infra.persistence.alert_models import (  # noqa: E402,F401
    AlertAttempt,
    AlertEventDecision,
    AlertFeedCursor,
    AlertIntent,
    FirstAlertIdentity,
    FirstAlertInventory,
    FirstEligibilityDecision,
    ManualConditionHistory,
)
from garimpei.infra.persistence.assessment_models import (  # noqa: E402,F401
    AssessmentHead,
    ConditionAssessment,
)
from garimpei.infra.persistence.exploration_models import ExplorationOffer, ExplorationRevision  # noqa: E402,F401
from garimpei.infra.persistence.identity_models import (  # noqa: E402,F401
    IdentityProgress,
    ManualIdentityRevision,
    ProductIdentification,
)
from garimpei.infra.persistence.integration_models import IntegrationSettings  # noqa: E402,F401
from garimpei.infra.persistence.media_models import (  # noqa: E402,F401
    MediaAsset,
    MediaCapture,
    MediaEntry,
    MediaJob,
    MediaReference,
)
from garimpei.infra.persistence.operations_models import (  # noqa: E402,F401
    BackupRecord,
    BackupSchedule,
    OperationalDiagnostic,
    OperationalUnit,
    RecoveryBarrier,
)
from garimpei.infra.persistence.operations_models import OperationalSnapshot as OperationalSnapshot  # noqa: E402
from garimpei.infra.persistence.research_models import (  # noqa: E402,F401
    ComparableInvestigation,
    InvestigationTarget,
    ResearchCandidateDecision,
    ResearchQuery,
)
