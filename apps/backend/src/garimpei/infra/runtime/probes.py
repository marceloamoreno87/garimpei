import json
from datetime import timedelta
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.db import DatabaseError, connection
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone

from garimpei.config.env import RuntimeConfig
from garimpei.infra.persistence.models import RuntimeState


class DatabaseProbe:
    def check(self) -> bool:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return bool(cursor.fetchone() == (1,))
        except DatabaseError:
            connection.close()
            return False


class MigrationsProbe:
    def check(self) -> bool:
        try:
            executor = MigrationExecutor(connection)
            return not executor.migration_plan(executor.loader.graph.leaf_nodes())
        except DatabaseError:
            return False


class WorkerProbe:
    def __init__(self, config: RuntimeConfig) -> None:
        self._config = config

    def check(self) -> bool:
        try:
            return RuntimeState.objects.filter(
                environment_id=self._config.environment_id,
                run_id=self._config.run_id,
                stopped_at__isnull=True,
                last_probe_at__gte=timezone.now() - timedelta(seconds=15),
            ).exists()
        except DatabaseError:
            return False


class WahaProbe:
    def __init__(self, config: RuntimeConfig) -> None:
        self._config = config

    def check(self) -> bool:
        request = Request(
            f"http://127.0.0.1:{self._config.waha_port}/health",
            headers={"X-Api-Key": self._config.waha_key},
        )
        try:
            with urlopen(request, timeout=2) as response:
                return bool(response.status == 200 and json.load(response).get("status") == "ok")
        except (URLError, OSError, ValueError):
            return False
