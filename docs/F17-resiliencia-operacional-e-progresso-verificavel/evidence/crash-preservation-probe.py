"""E2E-CRASH-01: existing facts, a manual choice and a receipt survive the same real SIGKILL."""

import argparse
import json
import os
import signal
from pathlib import Path

from garimpei.infra.runtime.processes import verify_process
from tests.factories.alert_scenario import alert_scenario, wait_alerts
from tests.factories.operations_metrics import InstanceMeasurements
from tests.factories.runtime import FoundationInstance
from tests.factories.valuation import listing
from tests.integration.test_collection import command, completed, sql, wait_for

PROTECTED = """
import json,hashlib
from garimpei.infra.persistence.listing_models import ManualCondition,Listing,ListingObservation
from garimpei.infra.persistence.alert_models import ManualConditionHistory,AlertIntent
choice=list(ManualCondition.objects.values())
history=list(ManualConditionHistory.objects.values())
receipt=list(AlertIntent.objects.filter(confirmed_message='message-1').values('id','body','session','recipient','account','confirmed_message','confirmed_at','confirmed_ack'))
assert len(choice)==1 and len(history)==1 and len(receipt)==1
row=Listing.objects.get(external_id='17801')
observation=OBSERVATION_ID or str(row.latest_id)
original=list(ListingObservation.objects.filter(pk=observation).values())
assert len(original)==1
protected={'choice':choice,'history':history,'receipt':receipt,'listing_id':str(row.id),'observation':original}
print(json.dumps({'sha256':hashlib.sha256(json.dumps(protected,sort_keys=True,default=str).encode()).hexdigest(),'choices':len(choice),'histories':len(history),'receipts':len(receipt),'observation_id':observation}))
"""


def protected(
    instance: FoundationInstance, observation_id: str | None = None
) -> dict[str, object]:
    result = instance.shell(PROTECTED.replace("OBSERVATION_ID", repr(observation_id)))
    assert result.returncode == 0, "Protected baseline inspection failed"
    return json.loads(result.stdout.strip().splitlines()[-1])


def kill_worker(instance: FoundationInstance) -> None:
    owner = next(
        row for row in instance.manifest["processes"] if "runworker" in row["command"]
    )
    verify_process(owner, instance.root)
    os.killpg(owner["pgid"], signal.SIGKILL)


def execute(directory: Path, boundary: str) -> dict[str, object]:
    private = directory / boundary
    private.mkdir(mode=0o700)
    with alert_scenario(private) as (instance, source, clock, channel):
        clock.advance(1)
        source.rows["17801"] = listing(
            "17801",
            "1000,00",
            published_at=clock.value.isoformat(),
            delivery=True,
            delivery_cep="01001000",
            pickup=False,
        )
        clock.advance(61)
        completed(instance, 2)
        wait_alerts(instance, 1, clock)
        choice = instance.shell(
            "from garimpei.main import build_classify_condition;from garimpei.infra.persistence.listing_models import Listing;assert build_classify_condition().execute(Listing.objects.get(external_id='614').id,'good',0)==1"
        )
        assert choice.returncode == 0, choice.stderr
        before = protected(instance)
        with InstanceMeasurements(
            instance, private / "metrics.json", mode="fault"
        ) as metrics:
            clock.advance(1)
            source.rows["17802"] = listing(
                "17802",
                "1000,00",
                published_at=clock.value.isoformat(),
                delivery=True,
                delivery_cep="01001000",
                pickup=False,
            )
            if boundary == "before_commit":
                with instance.database() as barrier:
                    barrier.execute("SELECT pg_advisory_lock(170019)")
                    sql(
                        instance,
                        """
                        CREATE FUNCTION f17_preservation_gate() RETURNS trigger LANGUAGE plpgsql AS $$
                        BEGIN
                          IF EXISTS(SELECT 1 FROM runtime_listing WHERE id=NEW.listing_id AND external_id='17802') THEN
                            PERFORM pg_advisory_xact_lock(170019);
                          END IF;
                          RETURN NEW;
                        END $$;
                        CREATE TRIGGER f17_preservation_gate BEFORE INSERT ON runtime_listingevent
                        FOR EACH ROW EXECUTE FUNCTION f17_preservation_gate();
                    """,
                    )
                    clock.advance(61)
                    wait_for(
                        lambda: bool(
                            sql(
                                instance,
                                "SELECT pid FROM pg_stat_activity WHERE datname=current_database() AND wait_event='advisory'",
                            )
                        ),
                        "publication before commit",
                    )
                    assert sql(
                        instance,
                        "SELECT count(*) FROM runtime_listing WHERE external_id='17802'",
                    ) == [(0,)]
                    kill_worker(instance)
                    sql(
                        instance,
                        "SELECT pg_cancel_backend(pid) FROM pg_stat_activity WHERE datname=current_database() AND wait_event='advisory'",
                    )
                    assert sql(
                        instance,
                        "SELECT count(*) FROM runtime_listing WHERE external_id='17802'",
                    ) == [(0,)]
                    barrier.execute("SELECT pg_advisory_unlock(170019)")
                sql(
                    instance,
                    "DROP TRIGGER f17_preservation_gate ON runtime_listingevent;DROP FUNCTION f17_preservation_gate()",
                )
            else:
                channel.hold_post = True
                clock.advance(61)
                assert channel.held.wait(30)
                assert sql(
                    instance,
                    "SELECT count(*) FROM runtime_listing l JOIN runtime_listingobservation o ON o.id=l.latest_id WHERE l.external_id='17802'",
                ) == [(1,)]
                kill_worker(instance)
                channel.release.set()
                channel.hold_post = False
            assert protected(instance, str(before["observation_id"])) == before
            command(instance, "./scripts/stop.sh")
            clock.advance(61)
            command(instance, "./scripts/init.sh", "--disposable")
            wait_alerts(instance, 2, clock)
            assert protected(instance, str(before["observation_id"])) == before
            assert sql(
                instance,
                "SELECT count(*) FROM runtime_listing WHERE external_id='17802'",
            ) == [(1,)]
            assert len(channel.messages) == 2
            assert len([call for call in channel.calls if call[0] == "POST"]) == 2
            metrics.observed.update(
                confirmed_posts=2,
                protected_choices=1,
                protected_history=1,
                protected_receipts=1,
            )
    return {
        "boundary": boundary,
        "verdict": "PASS",
        "real_sigkill": True,
        "protected_digest": before["sha256"],
        "protected_choices": 1,
        "protected_history": 1,
        "protected_receipts": 1,
        "new_listing_identities": 1,
        "posts": 2,
        "metrics": json.loads((private / "metrics.json").read_text()),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    directory = parser.parse_args().directory.resolve()
    directory.mkdir(mode=0o700, parents=True, exist_ok=False)
    results = []
    for boundary in ("before_commit", "after_commit_before_confirmation"):
        results.append(execute(directory, boundary))
        (directory / "crash-preservation.json").write_text(
            json.dumps({"item": "E2E-CRASH-01", "results": results}, indent=2) + "\n"
        )
