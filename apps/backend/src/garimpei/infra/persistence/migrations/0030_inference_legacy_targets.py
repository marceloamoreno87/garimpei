"""Preserve historical profile/cache identities while making their real targets explicit."""

from django.apps.registry import Apps
from django.db import migrations, models
from django.db.backends.base.schema import BaseDatabaseSchemaEditor

LEGACY = [
    "local-evidence-v1",
    "condition-evidence-v1",
    "condition-evidence-v2",
    "condition-evidence-v3",
    "condition-evidence-v4",
]


def backfill(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    request = apps.get_model("runtime", "InferenceRequest")
    request.objects.using(schema_editor.connection.alias).filter(
        prompt_version__in=LEGACY, observation__isnull=False
    ).update(
        target_kind="listing_observation",
        target_id=models.F("observation_id"),
        target_revision=models.F("revision"),
    )


def reverse_backfill(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    request = apps.get_model("runtime", "InferenceRequest")
    request.objects.using(schema_editor.connection.alias).filter(prompt_version__in=LEGACY).update(
        target_id=None, target_revision=None
    )


# Old emitters and immutable historical restore rows omit the new metadata. Fill
# only absent legacy metadata; an explicitly divergent target must still fail.
TRIGGER = """
CREATE FUNCTION garimpei_inference_legacy_target() RETURNS trigger AS $$
BEGIN
 IF NEW.prompt_version IN ('local-evidence-v1','condition-evidence-v1','condition-evidence-v2','condition-evidence-v3','condition-evidence-v4')
    AND NEW.target_kind='listing_observation' AND NEW.target_id IS NULL
    AND NEW.target_revision IS NULL AND NEW.observation_id IS NOT NULL THEN
  NEW.target_id := NEW.observation_id;
  NEW.target_revision := NEW.revision;
 END IF;
 RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER garimpei_inference_legacy_target
BEFORE INSERT OR UPDATE ON runtime_inferencerequest
FOR EACH ROW EXECUTE FUNCTION garimpei_inference_legacy_target();
"""
REVERSE_TRIGGER = """
DROP TRIGGER IF EXISTS garimpei_inference_legacy_target ON runtime_inferencerequest;
DROP FUNCTION IF EXISTS garimpei_inference_legacy_target();
"""


class Migration(migrations.Migration):
    dependencies = [("runtime", "0029_assistance_reviews")]
    operations = [
        migrations.RemoveConstraint(model_name="inferencerequest", name="inference_profile_target"),
        migrations.RunPython(backfill, reverse_backfill),
        migrations.RunSQL(TRIGGER, REVERSE_TRIGGER),
        migrations.AddConstraint(
            model_name="inferencerequest",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(
                        ("context", {}),
                        ("observation__isnull", False),
                        (
                            "prompt_version__in",
                            [
                                "local-evidence-v1",
                                "condition-evidence-v1",
                                "condition-evidence-v2",
                                "condition-evidence-v3",
                                "condition-evidence-v4",
                            ],
                        ),
                        ("target_id", models.F("observation_id")),
                        ("target_id__isnull", False),
                        ("target_kind", "listing_observation"),
                        ("target_revision", models.F("revision")),
                        ("target_revision__isnull", False),
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
