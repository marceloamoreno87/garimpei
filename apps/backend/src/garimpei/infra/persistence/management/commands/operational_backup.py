from argparse import ArgumentParser
from datetime import datetime
from typing import TypedDict, Unpack
from uuid import UUID, uuid4

from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError

from garimpei.config.env import ConfigurationError, load_config
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
            message = "Operação não concluída: " + reason
            if reason in {
                "restore_requires_owned_disposable_eval",
                "restore_requires_empty_disposable_eval",
            }:
                message = "A restauração exige destino eval isolado, próprio, descartável e vazio."
            raise CommandError(message, returncode=1) from None

    def _dispatch(self, options: Options) -> None:
        action = options["action"]
        if action == "restore" and load_config(require_secrets=False).environment != "eval":
            raise OperationsError("restore_requires_owned_disposable_eval")
        repository = build_backup_repository()
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
            recovery = repository.catalog().get("recovery")
            if isinstance(recovery, dict):
                self.stdout.write(
                    f"Origem: {recovery['source_installation']}; cópia de {_moment(recovery['snapshot_at'])}. "
                    f"Intervalo sem reconciliação: {_moment(recovery['snapshot_at'])} até {_moment(recovery['restored_at'])}."
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
            f"Última cópia concluída: {_moment(catalog['last_success_at'])}; próxima: {_moment(catalog['next_due_at'])}"
        )
        self.stdout.write(f"Última falha: {_moment(catalog.get('last_failure_at'))}")
        records = catalog["records"]
        if isinstance(records, list):
            for record in records:
                self.stdout.write(
                    f"{record['id']} · {record['state']} · {_moment(record['snapshot_at'])} · formato {record['format_version']} · restauração {record['restoration_state']} · {_scope_label(record.get('scope'))} · motivo {record.get('reason') or 'nenhum'}"
                )
        self.stdout.write(
            "Cópia no mesmo disco não cobre perda desse disco; acesso Facebook/WhatsApp exige recuperação separada."
        )


def _archive_argument(options: Options) -> str:
    if not options["archive"]:
        raise ValueError("archive required")
    return options["archive"]


def _moment(value: object) -> str:
    return value.isoformat() if isinstance(value, datetime) else "não informado"


def _scope_label(value: object) -> str:
    if not isinstance(value, dict) or not isinstance(value.get("counts"), dict):
        return "escopo não informado"
    counts = value["counts"]
    return f"{counts.get('runtime.listing', 'não medido')} anúncios; {counts.get('runtime.listingobservation', 'não medido')} observações"
