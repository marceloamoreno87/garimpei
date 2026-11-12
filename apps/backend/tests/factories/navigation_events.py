"""F13 integrated collection and fake-channel evidence; no real integration is used."""

import ctypes
import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

from tests.factories.alert import WahaServer, serve_waha
from tests.factories.alert_scenario import (
    AlertScenario,
    HistoricalAlertSource,
    seed_historical_comparators,
)
from tests.factories.listing import serve
from tests.factories.valuation import (
    prepare_valuation_instance,
    wait_valuation,
)
from tests.integration.test_collection import command, completed, configure


@dataclass
class NavigationValuationSource(HistoricalAlertSource):
    pro_rows: dict[str, dict[str, object]] = field(default_factory=dict)
    include_pro_in_active: bool = False

    def respond(self, path: str, parameters: dict[str, str]) -> tuple[int, dict[str, object]]:
        if path.startswith("/detail/") and path.removeprefix("/detail/") in self.pro_rows:
            self.calls.append((path, parameters.copy()))
            return 200, self.pro_rows[path.removeprefix("/detail/")] | {
                "context_cep": parameters["cep"]
            }
        if path == "/search" and parameters["term"] in {"PS5 Pro", "PlayStation 5 Pro"}:
            self.calls.append((path, parameters.copy()))
            return 200, dict(
                context={key: value for key, value in parameters.items() if key != "page"},
                cards=list(self.pro_rows.values()),
                next=None,
                end=True,
                empty=not self.pro_rows,
            )
        status, body = super().respond(path, parameters)
        if path == "/search" and self.include_pro_in_active:
            body["cards"] = [*cast(list[object], body["cards"]), *self.pro_rows.values()]
        return status, body


@contextmanager
def navigation_alert_scenario(
    private: Path,
) -> Iterator[tuple[AlertScenario, NavigationValuationSource]]:
    source, channel = NavigationValuationSource(), WahaServer()
    source.rows["699"]["description"] = "Com defeito. Não funciona."
    with serve(source) as url, serve_waha(channel) as waha:
        instance, clock = prepare_valuation_instance(
            Path(__file__).resolve().parents[4], private, url
        )
        with instance.private_file.open("a") as output:
            output.write(
                f"GARIMPEI_AI_SERVICE_ENABLED=false\nGARIMPEI_ALERTS_ENABLED=true\nGARIMPEI_ALERT_FIXTURE_URL={waha}\nGARIMPEI_WAHA_SESSION=synthetic\nGARIMPEI_WAHA_RECIPIENT=100@c.us\nGARIMPEI_WAHA_ACCOUNT=200@c.us\n"
            )
        command(instance, "./scripts/init.sh", "--disposable")
        try:
            seed_historical_comparators(instance, source)
            configure(instance)
            completed(instance, 1)
            wait_valuation(instance, price="2300.00")
            yield (instance, source, clock, channel), source
        finally:
            source.release.set()
            command(instance, "./scripts/stop.sh", "--clean")


class FileAccessCanary:
    """Linux IN_OPEN/IN_ACCESS records access to a synthetic secret requested by hostile text."""

    def __init__(self, path: Path) -> None:
        path.write_text("SYNTHETIC_F13_VALUE_DO_NOT_SEND")
        path.chmod(0o600)
        library = ctypes.CDLL(None, use_errno=True)
        descriptor = int(library.inotify_init1(os.O_NONBLOCK | os.O_CLOEXEC))
        if descriptor < 0:
            raise OSError(ctypes.get_errno(), "inotify_init1")
        result = int(library.inotify_add_watch(descriptor, os.fsencode(path), 0x1 | 0x20))
        if result < 0:
            os.close(descriptor)
            raise OSError(ctypes.get_errno(), "inotify_add_watch")
        self.path, self._descriptor = path, descriptor

    def accessed(self) -> bool:
        try:
            return bool(os.read(self._descriptor, 65536))
        except BlockingIOError:
            return False

    def close(self) -> None:
        os.close(self._descriptor)


def read_marker(output: str, marker: str) -> dict[str, object]:
    line = next(line for line in output.splitlines() if line.startswith(marker + "="))
    return cast(dict[str, object], json.loads(line[len(marker) + 1 :]))
