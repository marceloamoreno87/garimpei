from argparse import ArgumentParser
from typing import TypedDict, Unpack
from uuid import UUID, uuid4

from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError

from garimpei.config.env import ConfigurationError
from garimpei.domain.operations.errors import OperationsError
from garimpei.infra.gateway.operations.archive_gateway import ArchiveInvalid
from garimpei.main import build_backup_repository, build_create_backup, build_restore_backup


class Options(TypedDict):
    action: str
    id: str | None
    archive: str | None
    isolated: bool


class Command(BaseCommand):
    help = (
        "Create/export versioned private business copies or restore into an empty disposable eval."
    )

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("action", choices=["list", "create", "export", "restore", "verify"])
        parser.add_argument("--id")
        parser.add_argument("--archive")
        parser.add_argument("--isolated", action="store_true")

    def handle(self, *_args: str, **options: Unpack[Options]) -> None:
        try:
            self._dispatch(options)
        except (ValueError, ConfigurationError):
            raise CommandError(
                "Argumentos inválidos; use --id UUID ou --archive PATH conforme a ação.",
                returncode=64,
            ) from None
        except (OperationsError, ArchiveInvalid, OSError, DatabaseError) as error:
            reason = error.code if isinstance(error, OperationsError) else "operation_unavailable"
            raise CommandError("Operação não concluída: " + reason, returncode=1) from None

    def _dispatch(self, options: Options) -> None:
        repository = build_backup_repository()
        action = options["action"]
        if action == "list":
            self._list(repository.catalog())
            return
        if action == "create":
            self.stdout.write(f"Operação concluída: {build_create_backup().execute()}")
            return
        if action == "restore":
            identity = build_restore_backup().execute(
                _archive_argument(options), isolated=options["isolated"]
            )
            self.stdout.write(
                f"Dados restaurados: {identity}; despacho bloqueado até reconciliação. Recupere acesso Facebook/WhatsApp separadamente."
            )
            return
        if action == "export":
            identity = repository.export(UUID(options["id"] or ""), uuid4())
            self.stdout.write(f"Operação concluída: {identity}")
            return
        result = repository.verify(UUID(options["id"] or ""))
        self.stdout.write(
            f"Integridade verificada: {result['id']}. Restauração: {result['restoration_state']}."
        )

    def _list(self, catalog: dict[str, object]) -> None:
        self.stdout.write(
            f"Última cópia concluída: {catalog['last_success_at']}; próxima: {catalog['next_due_at']}"
        )
        records = catalog["records"]
        if isinstance(records, list):
            for record in records:
                self.stdout.write(
                    f"{record['id']} · {record['state']} · {record['snapshot_at']} · formato {record['format_version']} · restauração {record['restoration_state']}"
                )
        self.stdout.write(
            "Cópia no mesmo disco não cobre perda desse disco; acesso Facebook/WhatsApp exige recuperação separada."
        )


def _archive_argument(options: Options) -> str:
    if not options["archive"]:
        raise ValueError("archive required")
    return options["archive"]
