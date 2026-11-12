from tests.factories.runtime import FoundationInstance
from tests.integration.test_collection import shell
from tests.integration.test_operational_recovery import operational_instance as operational_instance


def test_additive_migration_preserves_business_history_without_inventing_progress(
    operational_instance: FoundationInstance,
) -> None:
    shell(
        operational_instance,
        """
from uuid import uuid4
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.utils.timezone import now
from garimpei.infra.persistence.alert_models import AlertIntent,ManualConditionHistory
from garimpei.infra.persistence.listing_models import Listing,ListingObservation,ManualCondition
from garimpei.infra.persistence.monitoring_models import MonitoringConfiguration
from garimpei.infra.persistence.valuation_models import ValuationEvaluation
from garimpei.infra.persistence.operations_models import OperationalUnit
listing=Listing.objects.get(external_id='16001')
ManualCondition.objects.create(listing=listing,choice='good',revision=1,updated_at=now())
ManualConditionHistory.objects.create(listing=listing,publication_order=listing.publication_order,choice='good',revision=1,confirmed_at=now())
AlertIntent.objects.create(id=uuid4(),session='synthetic',recipient='100@g.us',account='200@c.us',body='Synthetic preserved authorized body',state='confirmed',reason='receipt_confirmed',created_at=now(),next_action=now(),confirmed_at=now(),confirmed_message='synthetic-migration-receipt',confirmed_ack=2)
models=[MonitoringConfiguration,ListingObservation,ManualCondition,ManualConditionHistory,ValuationEvaluation,AlertIntent]
before={model._meta.label_lower:list(model.objects.order_by(model._meta.pk.name).values()) for model in models}
identities=list(Listing.objects.order_by('id').values_list('id','latest_id','ordinal'))
# Recreate the pre-F17 schema on this owned, paused synthetic database only.
executor=MigrationExecutor(connection)
executor.migrate([('runtime','0016_merge_navigation_and_first_eligibility')])
executor=MigrationExecutor(connection)
executor.migrate(executor.loader.graph.leaf_nodes())
after={model._meta.label_lower:list(model.objects.order_by(model._meta.pk.name).values()) for model in models}
assert after==before
assert list(Listing.objects.order_by('id').values_list('id','latest_id','ordinal'))==identities
assert not OperationalUnit.objects.exists()
assert AlertIntent.objects.filter(state='confirmed',confirmed_message='synthetic-migration-receipt').count()==1
""",
    )
