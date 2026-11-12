import time
from pathlib import Path

from tests.factories.media import generate_corpus, prepare_media_instance, serve_media


def test_real_media_worker_drains_originals_and_derivatives_without_thirty_second_gaps(
    tmp_path: Path,
) -> None:
    generate_corpus()
    with serve_media() as (origin, requests):
        instance = prepare_media_instance(Path(__file__).resolve().parents[4], tmp_path, origin)
        result = instance.command("./scripts/init.sh", "--disposable")
        assert result.returncode == 0, result.stdout + result.stderr
        try:
            result = instance.shell(
                "from tests.factories.media import seed_media_cases;from garimpei.main import reconcile_media;seed_media_cases("
                + repr(origin)
                + ");reconcile_media()"
            )
            assert result.returncode == 0, result.stdout + result.stderr
            deadline = time.monotonic() + 25
            with instance.database() as db:
                while time.monotonic() < deadline:
                    counts = db.execute(
                        "SELECT (SELECT count(*) FROM runtime_mediaasset WHERE state='available'),(SELECT count(*) FROM runtime_mediaasset WHERE thumbnail_state='ready')"
                    ).fetchone()
                    if counts and counts[0] == counts[1] == 13:
                        break
                    time.sleep(0.1)
                else:
                    raise AssertionError(("worker did not drain one-unit chain", counts))
                assert db.execute(
                    "SELECT count(*) FROM runtime_mediajob WHERE state='running'"
                ).fetchone() == (0,)
                assert db.execute(
                    "SELECT count(*) FROM runtime_mediajob WHERE kind='download' AND attempts>1"
                ).fetchone() == (0,)
                assert db.execute("SELECT count(*) FROM runtime_alertintent").fetchone() == (0,)
            assert len(requests) == 14
            assert all("Cookie" not in r and "Authorization" not in r for r in requests)
        finally:
            stopped = instance.command("./scripts/stop.sh", "--clean")
            assert stopped.returncode == 0, stopped.stdout + stopped.stderr
