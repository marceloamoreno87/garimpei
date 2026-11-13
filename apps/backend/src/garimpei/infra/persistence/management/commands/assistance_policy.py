"""Explicit adoption preserves legacy qualifications and frozen message bodies."""

import json
from argparse import ArgumentParser
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.timezone import now

from garimpei.config.env import load_config
from garimpei.infra.persistence.assistance_models import AssistancePolicy
from garimpei.infra.persistence.monitoring_unit_of_work import lock_monitoring_publication


class Command(BaseCommand):
    help = "Adotar política assistida após verificação, ou preparar avaliação isolada."

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("--activate", action="store_true")
        parser.add_argument("--evaluation", action="store_true")
        parser.add_argument("--verification", type=Path)

    def handle(self, *args: object, **options: object) -> None:
        config = load_config(require_secrets=False)
        if not options["activate"]:
            active = AssistancePolicy.objects.filter(pk=1, active=True).exists()
            self.stdout.write("Política assistida: " + ("ativa" if active else "aguardando adoção"))
            return
        evaluation = options["evaluation"] is True and config.environment == "eval"
        if not evaluation:
            _verification(config.root, options.get("verification"))
        with transaction.atomic():
            lock_monitoring_publication()
            AssistancePolicy.objects.update_or_create(
                pk=1, defaults=dict(active=True, adopted_at=now())
            )
        self.stdout.write("Política assistida adotada para novas decisões; histórico preservado.")


def _verification(root: Path, path: object) -> None:
    if not isinstance(path, Path):
        raise CommandError("Informe --verification com evidência humana e GPU verificada.")
    evidence = json.loads(path.read_text())
    progress = json.loads((root / "docs/prd_progress.json").read_text())
    if progress["features"]["F21"]["status"] != "done":
        raise CommandError("F21 conserva aceite real pendente; adoção integrada bloqueada.")
    if (
        not evidence.get("human_reviewer")
        or evidence.get("critical_regressions") != 0
        or evidence.get("gpu_profiles_verified") is not True
    ):
        raise CommandError(
            "Corpus humano, ausência de regressão crítica e GPU precisam estar verificados."
        )
