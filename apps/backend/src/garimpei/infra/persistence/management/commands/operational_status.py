from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError

from garimpei.domain.operations.errors import OperationsError
from garimpei.main import build_operational_status


class Command(BaseCommand):
    help = "Read a consistent snapshot of operational progress without changing business decisions."

    def handle(self, *_args: str, **_options: object) -> None:
        try:
            state = build_operational_status().execute()
        except (OperationsError, DatabaseError):
            raise CommandError("Diagnóstico indisponível; tente novamente.", returncode=1) from None
        self.stdout.write(
            f"Snapshot {state['snapshot_id']} · {state['as_of']} · revisão {state['scope_revision']}"
        )
        self.stdout.write(
            "Despacho bloqueado." if state["dispatch_suspended"] else "Sem barreira de restauração."
        )
        self.stdout.write("Acesso Facebook/WhatsApp é recuperado separadamente dos dados.")
