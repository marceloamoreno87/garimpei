"""Container DNS is explicit; admitting it must not admit arbitrary remote destinations."""

import pytest

from garimpei.domain.alert.alert import AlertPolicy
from garimpei.infra.gateway.alert.waha_gateway import WahaGateway
from garimpei.infra.gateway.integration.waha_session import WahaSessionGateway


def test_private_waha_dns_requires_explicit_runtime_capability() -> None:
    WahaSessionGateway("http://waha:3000", "synthetic", 3, internal_service=True)
    WahaGateway("http://waha:3000", "synthetic", AlertPolicy(), internal_service=True)
    with pytest.raises(ValueError):
        WahaSessionGateway("http://waha:3000", "synthetic", 3)
    with pytest.raises(ValueError):
        WahaGateway("http://waha:3000", "synthetic", AlertPolicy())


@pytest.mark.parametrize(
    "url",
    [
        "http://remote.invalid:3000",
        "http://waha:4000",
        "http://waha:3000/path",
        "http://waha:3000?key=private",
        "http://private:secret@waha:3000",
        "https://waha:3000",
    ],
)
def test_private_waha_capability_does_not_allow_remote_or_credentialed_origins(url: str) -> None:
    with pytest.raises(ValueError):
        WahaSessionGateway(url, "synthetic", 3, internal_service=True)
    with pytest.raises(ValueError):
        WahaGateway(url, "synthetic", AlertPolicy(), internal_service=True)
