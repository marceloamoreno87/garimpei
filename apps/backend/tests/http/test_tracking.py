import json
import socket
import subprocess
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen
from uuid import uuid4

from tests.factories.listing import CATEGORY, CEP, PRODUCT
from tests.factories.runtime import FoundationInstance
from tests.integration.test_collection import Scenario, command, completed, scenario, shell, sql

# pytest discovers the disposable instance fixture imported from the worker suite.
__all__ = ["scenario"]


@contextmanager
def failing_web(instance: FoundationInstance, private: Path) -> Iterator[str]:
    (private / "f04_failure.py").write_text(
        "import django\ndjango.setup()\n"
        "from tests.factories.monitoring import failure_application\n"
        "application = failure_application('save')\n"
    )
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    origin = f"http://127.0.0.1:{port}"
    with (private / "failing-web.log").open("w+") as log:
        process = subprocess.Popen(
            [
                ".venv/bin/gunicorn",
                "--bind",
                f"127.0.0.1:{port}",
                "--pythonpath",
                str(private),
                "f04_failure:application",
            ],
            cwd=instance.root / "apps/backend",
            env=instance.environment,
            stdout=log,
            stderr=log,
        )
        try:
            for _ in range(40):
                try:
                    with urlopen(origin + "/configuracao/interesses/", timeout=1):
                        break
                except URLError:
                    time.sleep(0.1)
            else:
                log.seek(0)
                raise AssertionError(log.read())
            yield origin
        finally:
            process.terminate()
            process.wait(timeout=10)


def test_browser_draft_rollback_and_collection_status(scenario: Scenario, tmp_path: Path) -> None:
    instance, source, clock = scenario
    origin = f"http://127.0.0.1:{instance.config.web_port}"
    session = f"-s=garimpei-f04-{uuid4().hex[:8]}"

    def browser(*args: str) -> None:
        result = instance.command("playwright-cli", session, *args, timeout=30)
        assert result.returncode == 0 and "### Error" not in result.stdout, (
            result.stdout + result.stderr
        )

    def run(body: str) -> None:
        browser("run-code", "async page => {" + body + "}")

    command(
        instance,
        "uv",
        "run",
        "--project",
        "apps/backend",
        "--frozen",
        "--no-sync",
        "python",
        "apps/backend/manage.py",
        "runtime_probe",
        "--wait",
    )
    browser("open", origin)
    try:
        run(f"""
const save = () => page.getByRole('button', {{name: 'Salvar e continuar'}}).click();
await page.locator('#cep').fill({json.dumps(CEP)});
await save();
if (await page.locator('#shipping_estimate').count()) throw new Error('Freight should not be required');
await page.locator('#resale_fee_percent').fill('12.50');
await save();
await page.locator('input[value="{CATEGORY}"]').check();
await page.locator('#new_product').fill({json.dumps(PRODUCT)});
await page.getByRole('button', {{name: 'Salvar rascunho'}}).click();
await page.locator('input[name="product_names[]"]').waitFor({{state:'attached'}});
""")
        time.sleep(4.2)
        assert source.calls == []
        shell(
            instance,
            """
from garimpei.main import build_read_monitoring_configuration
assert not build_read_monitoring_configuration().execute().configured
""",
        )
        with failing_web(instance, tmp_path) as failed_origin:
            run(f"""
await page.goto('{failed_origin}/configuracao/interesses/');
const [response] = await Promise.all([
  page.waitForResponse(response => response.url().endsWith('/configuracao/concluir/')),
  page.getByRole('button', {{name: 'Concluir configuração'}}).click(),
]);
if (response.status() !== 503) throw Error('Expected controlled save failure');
await page.locator('[data-error-code=CONFIGURATION_SAVE_FAILED]').waitFor({{timeout:5000}});
""")
            time.sleep(4.2)
            assert source.calls == []
            shell(
                instance,
                """
from garimpei.main import build_read_monitoring_configuration
assert not build_read_monitoring_configuration().execute().configured
""",
            )
        source.pause_path = "/search"
        run(f"""
await page.goto('{origin}/configuracao/interesses/');
await page.getByRole('button', {{name: 'Concluir configuração'}}).click();
await page.waitForURL('**/acompanhamento/');
""")
        assert source.held.wait(8)
        calls = len(source.calls)
        run(f"""
await page.reload();
await page.getByRole('heading', {{name:'Coleta inicial em andamento'}}).waitFor();
await page.getByRole('link', {{name:'Revisar configurações'}}).waitFor();
await page.screenshot({{path:{json.dumps(str(tmp_path / "coleta-inicial.png"))}}});
""")
        assert len(source.calls) == calls
        source.release.set()
        completed(instance, 1)
        assert {params["term"] for route, params in source.calls if route == "/search"} == {
            CATEGORY,
            PRODUCT,
        }
        assert sql(instance, "SELECT DISTINCT kind, silent FROM runtime_listingevent") == [
            ("initial_load", True)
        ]
        source.mode = "partial"
        clock.advance(61)
        completed(instance, 2, "partial")
        run(f"""
await page.reload();
await page.getByRole('heading', {{name:'Coleta parcial'}}).waitFor();
await page.getByText(/Última coleta completa/).waitFor();
await page.getByRole('link', {{name:'Revisar configurações'}}).waitFor();
await page.screenshot({{path:{json.dumps(str(tmp_path / "coleta-parcial.png"))}}});
await page.getByRole('link', {{name:'Revisar configurações'}}).click();
await page.waitForURL('**/configuracoes/');
""")
    finally:
        browser("close")
