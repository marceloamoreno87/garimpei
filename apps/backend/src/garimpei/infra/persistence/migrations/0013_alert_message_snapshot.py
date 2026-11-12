from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("runtime", "0012_opportunity_collection")]
    operations = [
        migrations.AddField(
            model_name="alertintent", name="financial", field=models.JSONField(default=dict)
        ),
        migrations.AddField(
            model_name="alertintent",
            name="body_format",
            field=models.CharField(blank=True, default="", max_length=40),
        ),
    ]
