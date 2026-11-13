"""Owned F21 JSON-lines lab with real PostgreSQL and explicitly synthetic I/O."""

import json
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from tests.factories.alert import WahaServer, serve_waha
from tests.factories.assessment_origin import serve_assessment_images
from tests.factories.listing import prepare_listing_instance, serve
from tests.factories.runtime import pause_worker, resume_worker
from tests.factories.valuation import ValuationSource
from tests.integration.test_collection import configure


def main() -> None:
    source, channel = ValuationSource(rows={}), WahaServer(recipient="100@g.us")
    with (
        TemporaryDirectory(prefix="garimpei-f21-lab-") as private,
        serve(source) as url,
        serve_waha(channel) as waha,
        serve_assessment_images() as (origin, _requests),
    ):
        directory = Path(private)
        instance, clock = prepare_listing_instance(Path(__file__).parents[4], directory, url)
        with instance.private_file.open("a") as output:
            output.write(
                f"GARIMPEI_AI_SERVICE_ENABLED=false\nGARIMPEI_ASSESSMENT_ENABLED=true\nGARIMPEI_MEDIA_ROOT={directory}/media\nGARIMPEI_MEDIA_BUDGET_BYTES=67108864\nGARIMPEI_MEDIA_MIN_FREE_BYTES=1048576\nGARIMPEI_MEDIA_EVAL_ORIGIN={origin}\nGARIMPEI_VALUATION_FIXTURE_URL={url}\nGARIMPEI_ALERTS_ENABLED=true\nGARIMPEI_ALERT_FIXTURE_URL={waha}\nGARIMPEI_WAHA_SESSION=synthetic\nGARIMPEI_WAHA_RECIPIENT=100@g.us\nGARIMPEI_WAHA_ACCOUNT=200@c.us\n"
            )
        initialized = instance.command("./scripts/init.sh", "--disposable", timeout=120)
        (directory / "init.txt").write_text(initialized.stdout + initialized.stderr)
        if initialized.returncode:
            raise RuntimeError("F21 lab init failed; private init.txt contains diagnostics")
        group = pause_worker(instance)
        try:
            configure(instance)
            os.environ.update(instance.environment)
            import django

            django.setup()
            from tests.factories.assessment import assessment_context
            from tests.factories.assessment_lab_actions import AssessmentLab
            from tests.factories.gold_alerts import GoldLab

            lab = GoldLab(
                AssessmentLab(instance, source, clock, origin, assessment_context(), group, {}),
                channel,
            )
            print(
                json.dumps(
                    dict(
                        ready=True,
                        url=f"http://127.0.0.1:{instance.config.web_port}",
                        private_file=str(instance.private_file),
                    )
                ),
                flush=True,
            )
            for line in sys.stdin:
                payload = json.loads(line)
                if payload.get("action") == "quit":
                    break
                try:
                    result = lab.action(payload)
                except Exception as error:
                    import traceback

                    traceback.print_exc(file=sys.stderr)
                    result = dict(state="error", error_class=type(error).__name__)
                print(json.dumps(result, default=str, ensure_ascii=False), flush=True)
        finally:
            resume_worker(group)
            stopped = instance.command("./scripts/stop.sh", "--clean", timeout=120)
            if stopped.returncode:
                raise RuntimeError("F21 own cleanup failed")


if __name__ == "__main__":
    main()
