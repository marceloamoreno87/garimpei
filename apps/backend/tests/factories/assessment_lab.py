"""Disposable JSON-lines F15 lab. No user profile, actual GPU or actual WhatsApp."""

import json
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from tests.factories.assessment_origin import serve_assessment_images
from tests.factories.listing import prepare_listing_instance, serve
from tests.factories.runtime import pause_worker, resume_worker
from tests.factories.valuation import ValuationSource
from tests.integration.test_collection import configure


def main() -> None:
    source = ValuationSource(rows={})
    with (
        TemporaryDirectory(prefix="garimpei-f15-lab-") as private,
        serve(source) as source_url,
        serve_assessment_images() as (origin, _requests),
    ):
        directory = Path(private)
        root = Path(__file__).parents[4]
        instance, clock = prepare_listing_instance(root, directory, source_url)
        with instance.private_file.open("a") as output:
            output.write(
                f"GARIMPEI_AI_SERVICE_ENABLED=false\nGARIMPEI_ASSESSMENT_ENABLED=true\nGARIMPEI_MEDIA_ROOT={directory}/media\nGARIMPEI_MEDIA_BUDGET_BYTES=67108864\nGARIMPEI_MEDIA_MIN_FREE_BYTES=1048576\nGARIMPEI_MEDIA_EVAL_ORIGIN={origin}\n"
            )
        started = instance.command("./scripts/init.sh", "--disposable", timeout=120)
        (directory / "init.txt").write_text(started.stdout + started.stderr)
        if started.returncode:
            raise RuntimeError("Owned lab init failed; private init.txt contains diagnostics")
        group = pause_worker(instance)
        try:
            configure(instance)
            os.environ.update(instance.environment)
            import django

            django.setup()
            from tests.factories.assessment import assessment_context
            from tests.factories.assessment_lab_actions import AssessmentLab

            lab = AssessmentLab(instance, source, clock, origin, assessment_context(), group, {})
            _emit(
                dict(
                    ready=True,
                    url=f"http://127.0.0.1:{instance.config.web_port}",
                    manifest=str(directory / "manifest.json"),
                    runtime="controlled_fake",
                )
            )
            (directory / "manifest.json").write_text(
                json.dumps(
                    dict(
                        root=str(root),
                        private_file=str(instance.private_file),
                        port=instance.config.web_port,
                        paused_group=group,
                    )
                )
            )
            for line in sys.stdin:
                payload = json.loads(line)
                if payload.get("action") == "quit":
                    break
                try:
                    _emit(lab.action(payload))
                except Exception as error:
                    _emit(dict(state="error", error_class=type(error).__name__))
        finally:
            # Resume only the verified process from this runtime before normal shutdown.
            from garimpei.infra.runtime.processes import verify_process

            owner = next(p for p in instance.manifest["processes"] if "runworker" in p["command"])
            verify_process(owner, instance.config.root)
            resume_worker(int(owner["pgid"]))
            result = instance.command("./scripts/stop.sh", "--clean", timeout=120)
            if result.returncode:
                raise RuntimeError("Owned lab cleanup failed")


def _emit(value: dict[str, object]) -> None:
    print(json.dumps(value, default=str, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
