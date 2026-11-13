import json
from dataclasses import asdict
from typing import override
from uuid import UUID

from django.core.management.base import BaseCommand, CommandParser

from garimpei.main import build_qualify_gold_alert


class Command(BaseCommand):
    help = "Avalia evidências existentes sem forçar qualificação ou enviar mensagem."

    @override
    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--listing", required=True, type=UUID)

    def handle(self, **options: object) -> None:
        decision = build_qualify_gold_alert().execute(UUID(str(options["listing"])))
        self.stdout.write(json.dumps(asdict(decision), default=str, ensure_ascii=False))
