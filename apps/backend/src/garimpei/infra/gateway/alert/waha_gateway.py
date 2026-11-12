import json
import re
from datetime import datetime
from http.client import HTTPConnection, HTTPException
from typing import cast
from urllib.parse import quote, urlencode, urlsplit

from garimpei.domain.alert.alert import AlertPolicy, Binding, Delivery, Outcome, Receipt
from garimpei.domain.alert.eligibility import verified_receipt


class WahaGateway:
    def __init__(self, url: str, key: str, policy: AlertPolicy) -> None:
        parsed = urlsplit(url)
        if parsed.scheme != "http" or parsed.hostname != "127.0.0.1" or not parsed.port:
            raise ValueError("WAHA requires an explicit loopback HTTP origin")
        self._host, self._port, self._key, self._policy = parsed.hostname, parsed.port, key, policy

    def _request(
        self, method: str, path: str, body: dict[str, object] | None = None
    ) -> tuple[int, object]:
        connection = HTTPConnection(self._host, self._port, timeout=self._policy.timeout)
        try:
            # Explicit connect separates non-transmission from ambiguous request failures.
            connection.connect()
        except OSError:
            connection.close()
            raise PreTransmissionFailure() from None
        try:
            connection.request(
                method,
                path,
                json.dumps(body).encode() if body is not None else None,
                {"X-Api-Key": self._key, "Content-Type": "application/json"},
            )
            response = connection.getresponse()
            payload = response.read(2_000_001)
            if len(payload) > 2_000_000:
                raise ValueError("WAHA response limit exceeded")
            return response.status, json.loads(payload)
        finally:
            connection.close()

    def check(self, binding: Binding) -> bool:
        try:
            status, body = self._request("GET", "/api/sessions/" + quote(binding.session, safe=""))
            if status != 200 or not isinstance(body, dict) or body.get("status") != "WORKING":
                return False
            me = body.get("me")
            return isinstance(me, dict) and me.get("id") == binding.account
        except (OSError, HTTPException, ValueError, PreTransmissionFailure):
            return False

    def send(self, delivery: Delivery) -> Outcome:
        try:
            status, body = self._request(
                "POST",
                "/api/sendText",
                {
                    "session": delivery.binding.session,
                    "chatId": delivery.binding.recipient,
                    "text": delivery.body,
                    "linkPreview": False,
                    "linkPreviewHighQuality": False,
                },
            )
            if not 200 <= status < 300:
                # No image-specific rejection is assumed safe without the real proof.
                return Outcome("uncertain", "provider_response_ambiguous")
            receipt = self._receipt(body, delivery)
            state = (
                "confirmed"
                if receipt and verified_receipt(receipt, delivery.binding, delivery.body)
                else "uncertain"
            )
            return Outcome(
                state, "send_response_ack" if state == "confirmed" else "ack_pending", receipt
            )
        except PreTransmissionFailure:
            return Outcome("safe_retry", "not_transmitted")
        except (OSError, HTTPException, ValueError):
            return Outcome("uncertain", "response_lost_or_incomplete")

    def reconcile(self, delivery: Delivery, now: datetime) -> Outcome:
        try:
            return self._lookup(delivery, now)
        except (OSError, HTTPException, ValueError, PreTransmissionFailure):
            return Outcome("uncertain", "history_query_failed")

    def _lookup(self, delivery: Delivery, now: datetime) -> Outcome:
        path = (
            "/api/"
            + quote(delivery.binding.session, safe="")
            + "/chats/"
            + quote(delivery.binding.recipient, safe="")
            + "/messages"
        )
        if delivery.message_id:
            status, body = self._request(
                "GET", path + "/" + quote(delivery.message_id, safe="") + "?downloadMedia=false"
            )
            receipt = self._receipt(body, delivery) if status == 200 else None
            if receipt is None or receipt.id != delivery.message_id:
                return Outcome("uncertain", "message_id_unverified")
            return self._outcome(receipt, delivery)
        matches: dict[str, Receipt] = {}
        truncated = False
        conflict = False
        for page in range(self._policy.history_pages):
            status, body = self._request(
                "GET",
                path
                + "?"
                + urlencode(
                    {
                        "limit": self._policy.history_limit,
                        "offset": page * self._policy.history_limit,
                        "filter.timestamp.gte": int(delivery.authorized_at.timestamp())
                        - self._policy.clock_margin,
                        "filter.timestamp.lte": int(now.timestamp()) + self._policy.clock_margin,
                        "downloadMedia": "false",
                    }
                ),
            )
            if status != 200 or not isinstance(body, list):
                return Outcome("uncertain", "history_query_failed")
            truncated = bool(body)
            conflict = self._collect(body, delivery, matches) or conflict
        if conflict or truncated or len(matches) != 1:
            return Outcome("uncertain", "history_ambiguous_or_incomplete")
        return self._outcome(next(iter(matches.values())), delivery)

    def _collect(self, body: list[object], delivery: Delivery, matches: dict[str, Receipt]) -> bool:
        conflict = False
        for item in body:
            receipt = self._receipt(item, delivery, exact=False)
            if receipt and "Ref. " + str(delivery.reference) in receipt.body.splitlines():
                conflict = self._remember(receipt, matches) or conflict
        return conflict

    @staticmethod
    def _remember(receipt: Receipt, matches: dict[str, Receipt]) -> bool:
        prior = matches.get(receipt.id)
        matches[receipt.id] = receipt
        return prior is not None and prior.body != receipt.body

    @staticmethod
    def _receipt(body: object, delivery: Delivery, *, exact: bool = True) -> Receipt | None:
        if not isinstance(body, dict):
            return None
        value = cast(dict[str, object], body)
        identity, text, ack = value.get("id"), value.get("body"), value.get("ack")
        if not isinstance(identity, str) or not isinstance(text, str):
            return None
        if value.get("fromMe") is not True:
            return None
        chat = _expected_chat(value, delivery)
        if chat is None:
            return None
        if exact and text != delivery.body:
            return None
        return Receipt(identity, True, str(chat), text, ack if type(ack) is int else 0)

    @staticmethod
    def _outcome(receipt: Receipt, delivery: Delivery) -> Outcome:
        if verified_receipt(receipt, delivery.binding, delivery.body):
            return Outcome("confirmed", "history_ack", receipt)
        return Outcome("uncertain", "ack_or_body_unverified", receipt)


class PreTransmissionFailure(Exception):
    pass


def _expected_chat(value: dict[str, object], delivery: Delivery) -> str | None:
    binding = delivery.binding
    if value.get("to") == binding.recipient and _own_jid(value.get("from"), binding.account):
        return binding.recipient
    # GOWS represents group messages with from=Chat and participant/to=Sender.
    if value.get("from") != binding.recipient:
        return None
    sender = value.get("participant") or value.get("to")
    if _own_jid(sender, binding.account):
        return binding.recipient
    raw = value.get("_data")
    info = raw.get("Info") if isinstance(raw, dict) else None
    if (
        not isinstance(info, dict)
        or info.get("Chat") != binding.recipient
        or info.get("IsFromMe") is not True
    ):
        return None
    # GOWS can store its own sender as a LID and expose the verified phone JID in SenderAlt.
    if sender and sender != info.get("Sender"):
        return None
    own = _own_jid(info.get("Sender"), binding.account) or _own_jid(
        info.get("SenderAlt"), binding.account
    )
    return binding.recipient if own else None


def _own_jid(value: object, expected: str) -> bool:
    if not isinstance(value, str):
        return False

    def canonical(raw: str) -> str:
        return re.sub(r":[0-9]+(?=@)", "", raw).replace("@s.whatsapp.net", "@c.us")

    return canonical(value) == canonical(expected)
