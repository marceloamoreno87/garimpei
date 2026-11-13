import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("runtime", "0027_gold_qualification")]
    operations = [
        migrations.AlterField(
            model_name="inferencerequest",
            name="observation",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="runtime.listingobservation",
            ),
        ),
        migrations.AddField(
            model_name="inferencerequest",
            name="target_kind",
            field=models.CharField(max_length=30, default="listing_observation"),
        ),
        migrations.AddField(
            model_name="inferencerequest", name="target_id", field=models.UUIDField(null=True)
        ),
        migrations.AddField(
            model_name="inferencerequest",
            name="target_revision",
            field=models.PositiveBigIntegerField(null=True),
        ),
        migrations.AddField(
            model_name="inferencerequest", name="context", field=models.JSONField(default=dict)
        ),
        migrations.AddConstraint(
            model_name="inferencerequest",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(
                        ("context", {}),
                        ("observation__isnull", False),
                        ("prompt_version__in", ["local-evidence-v1", "condition-evidence-v4"]),
                        ("target_id__isnull", True),
                        ("target_kind", "listing_observation"),
                        ("target_revision__isnull", True),
                    ),
                    models.Q(
                        ("observation__isnull", False),
                        (
                            "prompt_version__in",
                            [
                                "identity-review-v1",
                                "comparable-review-v1",
                                "investigation-support-v1",
                            ],
                        ),
                        ("target_id", models.F("observation_id")),
                        ("target_id__isnull", False),
                        ("target_kind", "listing_observation"),
                        ("target_revision", models.F("revision")),
                        ("target_revision__gt", 0),
                        ("target_revision__isnull", False),
                    ),
                    models.Q(
                        ("observation__isnull", True),
                        ("prompt_version", "investigation-support-v1"),
                        ("target_id__isnull", False),
                        ("target_kind", "interest"),
                        ("target_revision__gt", 0),
                        ("target_revision__isnull", False),
                    ),
                    models.Q(
                        ("observation__isnull", True),
                        ("prompt_version", "operations-support-v1"),
                        ("target_id__isnull", False),
                        ("target_kind", "operations_snapshot"),
                        ("target_revision__gt", 0),
                        ("target_revision__isnull", False),
                    ),
                    _connector="OR",
                ),
                name="inference_profile_target",
            ),
        ),
    ]
