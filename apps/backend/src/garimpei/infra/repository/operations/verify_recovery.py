"""Release only an owned eval barrier after complete inventory and original-binding F09 proof."""

import hashlib
import json
import os
import tempfile
from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path
from typing import cast
from uuid import UUID

from django.db import transaction
from django.utils import timezone

from garimpei.config.env import RuntimeConfig
from garimpei.domain.alert.alert import Binding, Delivery
from garimpei.domain.alert.ports import Messaging
from garimpei.domain.operations.errors import OperationsError
from garimpei.infra.gateway.operations.recovery_evidence import RecoveryEvidenceGateway
from garimpei.infra.persistence.alert_models import AlertFeedCursor, AlertIntent
from garimpei.infra.persistence.operations_models import RecoveryBarrier
from garimpei.infra.repository.alert.postgres_repository import PostgresAlertRepository
from garimpei.infra.repository.operations.maintenance_lock import maintenance_lock
from garimpei.infra.runtime.manifest import read_manifest


class VerifyRecoveryGateway:
    def __init__(
        self,
        config: RuntimeConfig,
        private_file: Path,
        evidence: RecoveryEvidenceGateway,
        alerts: PostgresAlertRepository,
        channel: Callable[[Binding], Messaging],
    ) -> None:
        self._config, self._file, self._evidence = config, private_file, evidence
        self._alerts, self._channel = alerts, channel

    def verify(self, identity: UUID) -> dict[str, object]:
        _owned_eval(self._config)
        with maintenance_lock():
            barrier = RecoveryBarrier.objects.filter(
                installation=self._config.environment_id, backup_id=identity
            ).first()
            if barrier is None or barrier.evidence.get("data_integrity") != "verified":
                raise OperationsError("recovery_data_integrity_unverified")
            proof = self._evidence.read(identity)
            entries, through = _validate_inventory(barrier, proof)
            for entry in entries:
                self._verify_entry(entry)
            self._complete(barrier, proof, through)
        return {
            "id": str(identity),
            "archive_integrity": "verified",
            "restoration_state": "verified",
            "dispatch_reconciliation": "verified",
        }

    def _verify_entry(self, entry: dict[str, object]) -> None:
        row = AlertIntent.objects.get(id=_proof_uuid(entry.get("id")))
        state = str(entry.get("state"))
        if state in {"queued", "blocked", "safe_retry"} and not row.attempts.exists():
            return
        if state != "confirmed" or not row.body:
            raise OperationsError("recovery_transmission_unresolved")
        if row.body != entry.get("body") or (row.session, row.recipient, row.account) != (
            entry.get("session"),
            entry.get("recipient"),
            entry.get("account"),
        ):
            raise OperationsError("recovery_original_binding_or_body_mismatch")
        self._confirm_receipt(row, entry)

    def _confirm_receipt(self, row: AlertIntent, entry: dict[str, object]) -> None:
        attempt = row.attempts.filter(id=_proof_uuid(entry.get("attempt_id"))).first()
        if attempt is None or attempt.generation != row.generation:
            raise OperationsError("recovery_authorization_inventory_gap")
        message_id = entry.get("message_id")
        if not isinstance(message_id, str) or not message_id:
            raise OperationsError("recovery_receipt_missing")
        if row.state == "confirmed" and row.confirmed_message != message_id:
            raise OperationsError("recovery_receipt_conflict")
        binding = Binding(row.session, row.recipient, row.account)
        delivery = Delivery(
            row.id,
            row.generation,
            binding,
            row.body,
            attempt.authorized_at,
            message_id,
            True,
            attempt.id,
        )
        outcome = self._channel(binding).reconcile(delivery, timezone.now())
        if outcome.state != "confirmed" or outcome.receipt is None:
            raise OperationsError("recovery_channel_history_incomplete")
        self._alerts.finish(delivery, outcome, timezone.now())
        row.refresh_from_db()
        if row.state != "confirmed" or row.confirmed_message != message_id:
            raise OperationsError("recovery_receipt_not_preserved")

    def _complete(
        self, barrier: RecoveryBarrier, proof: dict[str, object], through: datetime
    ) -> None:
        with transaction.atomic():
            barrier.state, barrier.reason = "reconciled", "original_binding_receipts_verified"
            barrier.evidence = barrier.evidence | {
                "restoration_state": "verified",
                "observed_through": through.isoformat(),
                "proof_sha256": hashlib.sha256(
                    json.dumps(proof, sort_keys=True).encode()
                ).hexdigest(),
            }
            barrier.save()
            AlertFeedCursor.objects.update(dispatch_suspended=False)
        _complete_marker(self._file, barrier.backup_id)


def _owned_eval(config: RuntimeConfig) -> None:
    manifest = read_manifest(config.directory)
    if config.environment != "eval" or manifest is None:
        raise OperationsError("recovery_verification_requires_owned_eval")
    if (
        not manifest["disposable"]
        or manifest["session_kind"] != "synthetic"
        or manifest["checkout"] != str(config.root)
    ):
        raise OperationsError("recovery_verification_requires_owned_eval")


def _validate_inventory(
    barrier: RecoveryBarrier, proof: dict[str, object]
) -> tuple[list[dict[str, object]], datetime]:
    if (
        proof.get("format_version") != 1
        or proof.get("complete") is not True
        or proof.get("backup_id") != str(barrier.backup_id)
        or proof.get("source_installation") != barrier.evidence.get("source_installation")
    ):
        raise OperationsError("recovery_evidence_incomplete")
    try:
        start = datetime.fromisoformat(str(proof["snapshot_at"]))
        through = datetime.fromisoformat(str(proof["observed_through"]))
    except (KeyError, ValueError):
        raise OperationsError("recovery_evidence_interval_invalid") from None
    if (
        start != barrier.snapshot_at
        or through.tzinfo is None
        or through < barrier.restored_at
        or through > timezone.now() + timedelta(seconds=5)
    ):
        raise OperationsError("recovery_evidence_interval_incomplete")
    entries = proof.get("intents")
    if not isinstance(entries, list) or any(not isinstance(entry, dict) for entry in entries):
        raise OperationsError("recovery_evidence_inventory_invalid")
    rows = cast(list[dict[str, object]], entries)
    identities = {str(row.get("id")) for row in rows}
    expected = {str(identity) for identity in AlertIntent.objects.values_list("id", flat=True)}
    if len(identities) != len(rows) or identities != expected:
        raise OperationsError("recovery_authorization_inventory_gap")
    return rows, through


def _complete_marker(file: Path, identity: UUID) -> None:
    descriptor, name = tempfile.mkstemp(prefix=".recovery-proof-", dir=file.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w") as output:
            os.fchmod(output.fileno(), 0o600)
            json.dump({"backup_id": str(identity), "state": "reconciled"}, output)
            output.flush()
            os.fsync(output.fileno())
        temporary.replace(file)
    finally:
        temporary.unlink(missing_ok=True)


def _proof_uuid(value: object) -> UUID:
    try:
        return UUID(str(value))
    except ValueError:
        raise OperationsError("recovery_evidence_identifier_invalid") from None
