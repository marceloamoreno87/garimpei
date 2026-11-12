from typing import ClassVar

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("runtime", "0015_navigation"),
        ("runtime", "0015_first_eligibility"),
    ]

    operations: ClassVar[list[migrations.operations.base.Operation]] = []
