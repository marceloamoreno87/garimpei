import json
from datetime import UTC, datetime

import pytest

from garimpei.domain.integration.values import FacebookSession, IntegrationError, group_id


def test_cookie_header_and_export_normalize_without_secret_repr() -> None:
    now = datetime(2026, 11, 11, tzinfo=UTC)
    value = FacebookSession.parse("Cookie: c_user=123; xs=synthetic-private-value", now)
    assert {x.name for x in value.cookies} == {"c_user", "xs"}
    assert "synthetic-private-value" not in repr(value)
    exported = [
        {
            "name": x.name,
            "value": x.value,
            "domain": ".facebook.com",
            "expirationDate": now.timestamp() + 60,
        }
        for x in value.cookies
    ]
    assert len(FacebookSession.parse(json.dumps(exported), now).cookies) == 2


@pytest.mark.parametrize(
    "raw",
    [
        "xs=synthetic",
        "c_user=123; xs=",
        "c_user=private; xs=synthetic",
        '[{"name":"c_user","value":"123","domain":"evil.example"},{"name":"xs","value":"synthetic"}]',
        '[{"name":"c_user","value":"123","expires":1},{"name":"xs","value":"synthetic"}]',
        "{invalid-private-value",
        '[{"name":"c_user","value":"123","expires":0},{"name":"xs","value":"synthetic"}]',
        '[{"name":"c_user","value":"123","expires":1e100},{"name":"xs","value":"synthetic"}]',
    ],
)
def test_invalid_cookies_rejected_without_echo(raw: str) -> None:
    with pytest.raises(IntegrationError) as caught:
        FacebookSession.parse(raw, datetime.now(UTC))
    assert "private-value" not in str(caught.value)
    assert "synthetic" not in str(caught.value)


def test_only_canonical_groups_are_destinations() -> None:
    assert group_id("12345@g.us") and group_id("12345-67890@g.us")
    assert not group_id("123@c.us") and not group_id("forged@g.us")
