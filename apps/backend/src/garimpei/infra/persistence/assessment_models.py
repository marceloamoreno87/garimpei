from django.db import models


class ConditionAssessment(models.Model):
    id = models.UUIDField(primary_key=True)
    listing = models.ForeignKey("Listing", on_delete=models.PROTECT, related_name="assessments")
    observation = models.ForeignKey(
        "ListingObservation", on_delete=models.PROTECT, related_name="assessments"
    )
    input_fingerprint = models.CharField(max_length=64)
    policy_version = models.CharField(max_length=80)
    prompt_version = models.CharField(max_length=80)
    schema_version = models.CharField(max_length=80)
    model_revision = models.CharField(max_length=100)
    input_snapshot = models.JSONField()
    generation = models.PositiveBigIntegerField()
    status = models.CharField(max_length=20, default="waiting")
    condition = models.CharField(max_length=10, default="uncertain")
    sufficient = models.BooleanField(default=False)
    reason = models.CharField(max_length=80, default="waiting_inference")
    inference_refs = models.JSONField(default=list)
    media_references = models.JSONField(default=list)
    result = models.JSONField(null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    analyzed_at = models.DateTimeField(null=True)
    publication_order = models.PositiveBigIntegerField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["listing", "observation", "input_fingerprint"],
                name="condition_assessment_input",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    status__in=["waiting", "running", "complete", "partial", "failed", "superseded"]
                ),
                name="condition_assessment_status",
            ),
            models.CheckConstraint(
                condition=models.Q(condition__in=["good", "defect", "uncertain"]),
                name="condition_assessment_condition",
            ),
            models.CheckConstraint(
                condition=~models.Q(condition="good")
                | models.Q(sufficient=True, status="complete"),
                name="condition_good_requires_sufficient",
            ),
        ]
        indexes = [
            models.Index(fields=["listing", "created_at"]),
            models.Index(fields=["status", "updated_at"]),
            models.Index(fields=["listing", "publication_order"]),
        ]


class AssessmentHead(models.Model):
    listing = models.OneToOneField(
        "Listing", primary_key=True, on_delete=models.PROTECT, related_name="assessment_head"
    )
    observation = models.ForeignKey("ListingObservation", on_delete=models.PROTECT)
    input_fingerprint = models.CharField(max_length=64)
    generation = models.PositiveBigIntegerField(default=1)
    current = models.ForeignKey(
        ConditionAssessment, null=True, on_delete=models.PROTECT, related_name="+"
    )
    confirmed = models.ForeignKey(
        ConditionAssessment, null=True, on_delete=models.PROTECT, related_name="+"
    )
    updated_at = models.DateTimeField()
