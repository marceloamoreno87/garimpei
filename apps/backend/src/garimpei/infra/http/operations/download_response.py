from uuid import UUID

from django.http import FileResponse

from garimpei.domain.operations.download import ArchiveDownload


class LeasedFileResponse(FileResponse):
    def __init__(self, download: ArchiveDownload, identity: UUID) -> None:
        self._download, self._released = download, False
        super().__init__(
            download.stream, as_attachment=True, filename=f"garimpei-dados-{identity}.tar.gz"
        )
        self["Content-Length"] = str(download.size)
        self["ETag"] = '"' + download.sha256 + '"'

    def close(self) -> None:
        if self._released:
            return
        self._released = True
        try:
            super().close()
        finally:
            self._download.close()
