import re
from uuid import UUID, uuid4

from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBase,
    HttpResponseNotAllowed,
    JsonResponse,
)
from django.shortcuts import render

from garimpei.domain.operations.errors import OperationsError
from garimpei.domain.operations.ports import BackupRepository
from garimpei.infra.http.operations.download_response import LeasedFileResponse
from garimpei.infra.http.operations.presentation import status_context
from garimpei.usecase.operations.export_backup_usecase import ExportBackupUseCase
from garimpei.usecase.operations.read_status_usecase import ReadOperationalStatusUseCase
from garimpei.usecase.operations.resume_stage_usecase import ResumeStageUseCase


class OperationsHandler:
    def __init__(
        self,
        read: ReadOperationalStatusUseCase,
        resume: ResumeStageUseCase,
        export: ExportBackupUseCase,
        backups: BackupRepository,
    ) -> None:
        self._read, self._resume, self._export, self._backups = read, resume, export, backups

    def handle(
        self,
        request: HttpRequest,
        *,
        action: str = "status",
        stage: str = "",
        identity: UUID | None = None,
    ) -> HttpResponseBase:
        method = "POST" if action in {"resume", "export"} else "GET"
        if request.method != method:
            return HttpResponseNotAllowed([method])
        if action == "status":
            return _status(request, self._read)
        if action == "backups":
            return _private(
                render(
                    request,
                    "operations/backups.html",
                    self._backups.catalog() | {"request_id": str(uuid4())},
                )
            )
        if action == "resume":
            self._resume.execute(
                _uuid(request.POST.get("unidade")),
                _stage(stage),
                _revision(request.POST.get("revisao")),
            )
            return _redirect("/acompanhamento/#operational-status")
        if action == "export":
            assert identity is not None
            operation = self._export.execute(identity, _uuid(request.POST.get("request_id")))
            return _redirect(f"/acompanhamento/backups/?operacao={operation}")
        assert identity is not None
        return _download(self._backups, identity)


def _status(request: HttpRequest, read: ReadOperationalStatusUseCase) -> HttpResponse:
    if request.GET.get("versao"):
        _uuid(request.GET.get("versao"))
        raise OperationsError("operational_snapshot_expired")
    result = read.execute(request.GET.get("interesse"))
    if request.GET.get("formato") == "html":
        return _private(render(request, "operations/status.html", status_context(result)))
    return _private(JsonResponse(result))


def _download(backups: BackupRepository, identity: UUID) -> LeasedFileResponse:
    return _private(LeasedFileResponse(backups.download(identity), identity))


def _private[T: HttpResponseBase](response: T) -> T:
    response["Cache-Control"] = "no-store"
    response["X-Content-Type-Options"] = "nosniff"
    response["Referrer-Policy"] = "same-origin"
    return response


def _redirect(path: str) -> HttpResponse:
    return _private(HttpResponse(status=303, headers={"Location": path}))


def _uuid(value: str | None) -> UUID:
    if (
        value is None
        or re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", value)
        is None
    ):
        raise OperationsError("operational_uuid_invalid", 400)
    return UUID(value)


def _revision(value: str | None) -> int:
    if value is None or not value.isascii() or not value.isdecimal() or len(value) > 18:
        raise OperationsError("operational_revision_invalid", 400)
    return int(value)


def _stage(value: str) -> str:
    if value not in {
        "listing",
        "valuation",
        "alert",
        "exploration",
        "maintenance",
        "inference",
        "media",
    }:
        raise OperationsError("operational_stage_invalid", 400)
    return value
