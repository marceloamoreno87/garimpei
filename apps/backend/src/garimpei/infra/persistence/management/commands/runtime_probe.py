from argparse import ArgumentParser
from typing import TypedDict, Unpack

from django.core.management.base import BaseCommand, CommandError

from garimpei.config.env import load_config
from garimpei.infra.worker.probe_service import enqueue_manual, wait_probe


class ProbeOptions(TypedDict):
    wait: bool


class Command(BaseCommand):
    help = "Enqueue a technical receipt; never contact marketplaces or WhatsApp."

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("--wait", action="store_true")

    def handle(self, *_args: str, **options: Unpack[ProbeOptions]) -> None:
        config = load_config()
        probe = enqueue_manual(config)
        if options["wait"] and not wait_probe(probe, config.startup_timeout):
            raise CommandError("Runtime probe: receipt timeout")
        self.stdout.write(f"Probe {probe.id}: {'completed' if options['wait'] else 'queued'}")
