from uuid import UUID

from django.http import HttpRequest, HttpResponse, HttpResponseNotAllowed

from garimpei.domain.listing.exploration import Criteria
from garimpei.domain.media.errors import MediaError
from garimpei.domain.media.ports import MediaQueries, MediaStore
from garimpei.infra.http.listing.exploration_presentation import url
from garimpei.usecase.media.request_recovery_usecase import RequestMediaRecoveryUseCase


class MediaHandler:
    def __init__(
        self, queries: MediaQueries, store: MediaStore, recovery: RequestMediaRecoveryUseCase
    ) -> None:
        self._queries, self._store, self._recovery = queries, store, recovery

    def handle(
        self, request: HttpRequest, identity: UUID, version: UUID | None = None, variant: str = ""
    ) -> HttpResponse:
        if version is not None:
            return self._file(request, identity, version, variant)
        if request.method != "POST":
            return HttpResponseNotAllowed(["POST"])
        capture, revision = (
            request.POST.get("media_capture", ""),
            request.POST.get("media_revision", ""),
        )
        if (
            not _uuid(capture)
            or not revision.isdecimal()
            or len(revision) > 12
            or int(revision) < 1
        ):
            raise MediaError("MEDIA_INVALID_INPUT", 400)
        criteria = Criteria.parse(request.GET)
        self._recovery.execute(identity, UUID(capture), int(revision))
        response = HttpResponse(status=303)
        response["Location"] = url(criteria, f"/ofertas/{identity}/") + "&midia=solicitada"
        return response

    def _file(
        self, request: HttpRequest, listing: UUID, version: UUID, variant: str
    ) -> HttpResponse:
        if request.method not in {"GET", "HEAD"}:
            return HttpResponseNotAllowed(["GET", "HEAD"])
        file = self._queries.file(listing, version, variant)
        data = self._store.read(file)
        etag = '"' + file.sha256 + '"'
        cached = request.headers.get("If-None-Match") == etag
        response = HttpResponse(
            b"" if request.method == "HEAD" or cached else data,
            status=304 if cached else 200,
            content_type=file.mime,
        )
        if not cached:
            response["Content-Length"] = str(file.byte_count)
        response["ETag"] = etag
        response["X-Content-Type-Options"] = "nosniff"
        response["Cache-Control"] = "private, no-cache"
        return response


def _uuid(value: str) -> bool:
    import re

    return re.fullmatch(r"[a-fA-F0-9]{8}(?:-[a-fA-F0-9]{4}){3}-[a-fA-F0-9]{12}", value) is not None
