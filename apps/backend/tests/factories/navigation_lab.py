"""Disposable UI laboratory, owned by a foreground process and stopped on SIGTERM."""

import json
import signal
import sys
from pathlib import Path
from threading import Event

from tests.factories.listing import serve
from tests.factories.navigation import NavigationSourceFake, prepare_navigation_instance
from tests.factories.runtime import pause_worker, resume_worker
from tests.integration.test_navigation import BOOTSTRAP


def main(directory: Path) -> None:
    directory.mkdir(mode=0o700, exist_ok=True)
    root = Path(__file__).resolve().parents[4]
    stopped = Event()
    signal.signal(signal.SIGTERM, lambda *_: stopped.set())
    signal.signal(signal.SIGINT, lambda *_: stopped.set())
    with serve(NavigationSourceFake()) as url:
        instance = prepare_navigation_instance(root, directory, url)
        result = instance.command("./scripts/init.sh", "--disposable")
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)
        group = pause_worker(instance)
        try:
            result = instance.shell(
                BOOTSTRAP
                + """
from datetime import timedelta
first=nav.claim(attempt,scope,pages=2,details=False)
nav.page(attempt,first,source.search(scope,first.search,first.cursor))
first_detail=nav.claim(attempt,scope,pages=0,details=True)
nav.detail(attempt,first_detail,source.detail(scope,first_detail.target.external_id))
rows=list(NavigationWork.objects.order_by('origin_interest','front'))
for row,phase,reason in zip(rows,('running','waiting','partial','complete'),('','source_rate_limit','window_limit','')):
    row.phase,row.reason=phase,reason
    row.last_progress_at=now()-timedelta(seconds=40)
    row.next_attempt_at=now()+timedelta(seconds=90) if phase=='waiting' else None
    row.save()
    checkpoint=NavigationCheckpoint.objects.get(work=row)
    checkpoint.pages,checkpoint.details=(100 if phase=='partial' else 2),1
    checkpoint.term_index=1 if row.original_term=='PlayStation 5 Slim' and row.front=='discovery' else 0
    checkpoint.save()
query=next(query for query in scope.searches if query.term=='PlayStation 5 Slim')
suggestion=NicheSuggestion.objects.create(configuration_id=scope.configuration_id,revision=scope.revision,origin_interest=query.key,original_term=query.term,term='PS5 Pro',relation_key='ps5-slim-pro',catalog_version='2026-11-12.1',relation_reason='Outro modelo da família PlayStation 5; produto diferente, sem equivalência automática.',state='supported',observed_at=now())
SuggestionEvidence.objects.create(suggestion=suggestion,source=scope.source,external_id='1304',canonical_url='https://www.facebook.com/marketplace/item/1304/',excerpt='PS5 Pro funcionando',observed_at=now(),context_hash=scope.key,catalog_version='2026-11-12.1')
"""
            )
            if result.returncode:
                raise RuntimeError(result.stdout + result.stderr)
            (directory / "lab.json").write_text(
                json.dumps(
                    {
                        "url": f"http://127.0.0.1:{instance.config.web_port}",
                        "private_file": str(instance.private_file),
                    }
                )
            )
            while not stopped.wait(1):
                pass
        finally:
            with instance.database() as database:
                database.execute(
                    "DELETE FROM procrastinate_jobs WHERE status='todo' AND task_name IN ('garimpei.collect_listings','garimpei.navigation_suggestions')"
                )
            resume_worker(group)
            result = instance.command("./scripts/stop.sh", "--clean")
            if result.returncode:
                raise RuntimeError(result.stdout + result.stderr)


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve())
