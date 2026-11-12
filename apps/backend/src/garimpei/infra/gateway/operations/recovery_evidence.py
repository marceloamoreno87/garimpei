"""The owned eval laboratory can supply authoritative interval inventory; no real fallback."""

import json
from http.client import HTTPConnection, HTTPException
from typing import cast
from urllib.parse import urlencode, urlsplit
from uuid import UUID

from garimpei.domain.operations.errors import OperationsError


class RecoveryEvidenceGateway:
    def __init__(self, fixture_url: str | None) -> None:
        self._url = fixture_url

    def read(self, backup_id: UUID) -> dict[str, object]:
        if self._url is None:
            raise OperationsError("recovery_interval_completeness_unproven")
        parsed = urlsplit(self._url)
        if parsed.hostname != "127.0.0.1" or parsed.scheme != "http" or parsed.port is None:
            raise OperationsError("recovery_evidence_origin_invalid")
        connection = HTTPConnection("127.0.0.1", parsed.port, timeout=10)
        try:
            connection.request("GET", "/recovery?" + urlencode({"backup": str(backup_id)}))
            response = connection.getresponse()
            if response.status != 200:
                raise OperationsError("recovery_evidence_unavailable")
            payload = response.read(4 * 1024**2 + 1)
            if len(payload) > 4 * 1024**2:
                raise OperationsError("recovery_evidence_partial")
            value = json.loads(payload)
            if not isinstance(value, dict):
                raise OperationsError("recovery_evidence_invalid")
            return cast(dict[str, object], value)
        except (OSError, HTTPException, ValueError):
            raise OperationsError("recovery_evidence_unavailable") from None
        finally:
            connection.close()
