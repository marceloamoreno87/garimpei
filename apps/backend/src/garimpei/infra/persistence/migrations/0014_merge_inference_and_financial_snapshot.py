"""Join the independent inference and financial snapshot migration branches."""

from typing import ClassVar

from django.db import migrations
from django.db.migrations.operations.base import Operation


class Migration(migrations.Migration):
    dependencies = [
        ("runtime", "0013_alert_message_snapshot"),
        ("runtime", "0013_local_inference"),
    ]

    operations: ClassVar[list[Operation]] = []
