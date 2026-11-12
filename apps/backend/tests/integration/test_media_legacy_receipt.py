from pathlib import Path

from tests.factories.first_eligibility import first_eligibility_scenario
from tests.factories.media import serve_media
from tests.factories.runtime import pause_worker, resume_worker
from tests.integration.test_collection import command, completed, shell, sql, wait_for
from tests.integration.test_first_eligibility import target_messages, wait_first


def test_legacy_media_restart_preserves_manual_history_and_confirmed_fake_receipt(
    tmp_path: Path,
) -> None:
    with (
        serve_media() as (origin, requests),
        first_eligibility_scenario(tmp_path) as (
            instance,
            source,
            clock,
            channel,
        ),
    ):
        group = pause_worker(instance)
        try:
            shell(
                instance,
                """
from garimpei.main import build_read_condition,build_classify_condition
from garimpei.infra.persistence.listing_models import Listing
l=Listing.objects.get(external_id='16001');c=build_read_condition().execute(l.id)
build_classify_condition().execute(l.id,'good',c.state.revision)
assert l.latest.evidence.get('image_url') is None and l.latest.evidence.get('media') is None
""",
            )
        finally:
            resume_worker(group)
        source.rows["16001"]["description"] = "Usado. Funciona perfeitamente."
        clock.advance(61)
        completed(instance, 2)
        wait_first(channel, clock)
        group = pause_worker(instance)
        try:
            queries = {
                "observations": "SELECT id,price FROM runtime_listingobservation ORDER BY id",
                "events": "SELECT id,kind FROM runtime_listingevent ORDER BY id",
                "manual": "SELECT listing_id,choice,revision FROM runtime_manualcondition ORDER BY listing_id",
                "history": "SELECT listing_id,choice,revision FROM runtime_manualconditionhistory ORDER BY id",
                "receipt": "SELECT id,state,confirmed_message,confirmed_ack,confirmed_at FROM runtime_alertintent ORDER BY id",
            }
            before = {key: sql(instance, query) for key, query in queries.items()}
            assert any(row[1] == "confirmed" and row[2] for row in before["receipt"])
            messages = target_messages(channel).copy()
        finally:
            resume_worker(group)
        command(instance, "./scripts/stop.sh")
        with instance.private_file.open("a") as output:
            output.write(
                f"GARIMPEI_MEDIA_ROOT={tmp_path / 'media'}\nGARIMPEI_MEDIA_BUDGET_BYTES=67108864\nGARIMPEI_MEDIA_MIN_FREE_BYTES=1048576\nGARIMPEI_MEDIA_EVAL_ORIGIN={origin}\n"
            )
        source.rows["16001"]["media"] = dict(
            presence="present",
            complete=True,
            reason="",
            photos=[
                dict(
                    key="legacy-confirmed-photo",
                    primary=True,
                    correlated=True,
                    variants=[dict(url=origin + "/other.png", width=900, height=900)],
                )
            ],
        )
        clock.advance(61)
        command(instance, "./scripts/init.sh", "--disposable")
        completed(instance, 3)
        shell(
            instance,
            "from garimpei.main import reconcile_media;reconcile_media()",
        )
        wait_for(
            lambda: (
                sql(
                    instance,
                    "SELECT count(*) FROM runtime_mediaasset a JOIN runtime_listing l ON l.id=a.listing_id WHERE l.external_id='16001' AND a.state='available' AND a.thumbnail_state='ready'",
                )
                == [(1,)]
            ),
            "legacy photo and independent derivative",
            seconds=25,
        )
        # A restart after acquisition must not duplicate bytes or reopen the receipt.
        command(instance, "./scripts/stop.sh")
        command(instance, "./scripts/init.sh", "--disposable")
        shell(
            instance,
            "from garimpei.main import build_alert_handler;[build_alert_handler(stage).execute() for stage in ('adopt','refresh','reconcile','send')]",
        )
        for key in ("events", "manual", "history", "receipt"):
            assert sql(instance, queries[key]) == before[key], key
        after = sql(instance, queries["observations"])
        assert set(before["observations"]) <= set(after)
        assert target_messages(channel) == messages
        assert len(requests) == 1
        assert "Cookie" not in requests[0] and "Authorization" not in requests[0]
