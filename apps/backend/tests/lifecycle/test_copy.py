import json
import uuid
from pathlib import Path

from tests.factories.runtime import prepare_checkout_copy, prepare_instance


def test_migration_creation_and_unexpected_http_error_in_owned_copy(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[4]
    copy = prepare_checkout_copy(root, tmp_path)
    backend = copy / "apps/backend"
    urls = backend / "src/garimpei/infra/http/urls.py"
    urls.write_text(
        urls.read_text()
        + '\nfrom django.http import HttpRequest, HttpResponse\ndef foundation_fault(_request: HttpRequest) -> HttpResponse:\n    raise RuntimeError("private-unexpected-error-canary")\nurlpatterns += [path("foundation-fault", foundation_fault)]\n'
    )
    instance = prepare_instance(copy, tmp_path, "copy_" + uuid.uuid4().hex[:10])
    result = instance.command("./scripts/init.sh", "--disposable")
    assert result.returncode == 0, result.stdout + result.stderr
    try:
        model = backend / "src/garimpei/infra/persistence/models.py"
        model.write_text(
            model.read_text().replace(
                "class RuntimeState(models.Model):",
                'class RuntimeState(models.Model):\n    diagnostic_note = models.CharField(max_length=10, default="")',
            )
        )
        migrations = model.parent / "migrations"
        existing = set(migrations.glob("[0-9]*.py"))
        result = instance.command("./scripts/migrate-dev.sh", "--make", "foundation_probe")
        assert result.returncode == 0, result.stdout + result.stderr
        generated = set(migrations.glob("[0-9]*.py")) - existing
        assert len(generated) == 1 and next(iter(generated)).name.endswith("_foundation_probe.py")
        assert instance.command("./scripts/migrate-dev.sh", "--check").returncode == 1
        with instance.database() as connection:
            assert connection.execute(
                "SELECT count(*) FROM information_schema.columns WHERE table_name='runtime_runtimestate' AND column_name='diagnostic_note'"
            ).fetchone() == (0,)
        status, _, body = instance.http("/foundation-fault")
        assert status == 500
        assert json.loads(body) == {"error": {"code": "INTERNAL_ERROR"}}
        assert "private-unexpected-error-canary" not in body
        secrets = dict(
            line.split("=", 1) for line in instance.private_file.read_text().splitlines()
        )
        for name in ["web", "worker"]:
            text = (instance.config.directory / f"{name}.log").read_text()
            assert "private-unexpected-error-canary" not in text
            for key in ["DJANGO_SECRET_KEY", "POSTGRES_PASSWORD", "WAHA_API_KEY"]:
                assert secrets[key] not in text
            logs = [json.loads(line) for line in text.splitlines() if line.strip()]
            assert logs
            assert all(
                {"timestamp", "level", "logger", "event", "environment_id", "run_id"} <= log.keys()
                for log in logs
            )
    finally:
        result = instance.command("./scripts/stop.sh", "--clean")
        assert result.returncode == 0, result.stdout + result.stderr
