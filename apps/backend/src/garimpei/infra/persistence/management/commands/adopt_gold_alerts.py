import json
from typing import override

from django.core.management.base import BaseCommand, CommandParser

from garimpei.main import build_adopt_gold_policy


class Command(BaseCommand):
    help = (
        "Adota a qualificação gold-alert-v1, preservando corpos, recibos e transmissões incertas."
    )

    @override
    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--activate",
            required=True,
            action="store_true",
            help="Ativar a barreira persistente após atualizar os consumidores pelo lifecycle próprio.",
        )

    def handle(self, **_options: object) -> None:
        inventory = build_adopt_gold_policy().execute()
        self.stdout.write(
            json.dumps(
                dict(policy="gold-alert-v1", state="active", inventory=inventory),
                ensure_ascii=False,
            )
        )
