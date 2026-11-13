"""Observed regressions: bounded candidate fairness and source/manual provenance."""

from tests.factories.runtime import FoundationInstance
from tests.integration.test_inference import run_assert

SELECTION = r"""
import json
from decimal import Decimal
from uuid import UUID
from django.utils.timezone import now
from garimpei.domain.listing.listing import Evidence
from garimpei.infra.persistence.listing_models import Listing,ListingObservation
from garimpei.infra.persistence.assistance_models import AssistanceReview
from tests.factories.assistance import seed_observation
from garimpei.infra.repository.listing.mapper import encode_evidence
from garimpei.infra.repository.assistance.postgres_repository import PostgresAssistanceRepository
from garimpei.infra.gateway.assistance.snapshots import observation_snapshot,digest
from garimpei.infra.repository.assistance.publication import current_review

seed,_=seed_observation('selection-regression','text')
cycle=ListingObservation.objects.get(pk=seed).cycle

def listing(number,title):
 row=Listing.objects.create(id=UUID(int=number),source='f23-selection',external_id=str(number),canonical_url='https://example.invalid/'+str(number),first_seen_at=now(),origin='synthetic')
 evidence=Evidence(title=title,description='Usado. Funcionando perfeitamente.',condition='Usado — seminovo',source_available=True)
 observation=ListingObservation.objects.create(listing=row,cycle=cycle,ordinal=1,observed_at=now(),price=Decimal('2000'),evidence=encode_evidence(evidence),coverage={})
 row.latest=observation;row.save(update_fields=['latest'])
 return row

irrelevant=[listing(i,'iPhone 15 128GB') for i in range(1,13)]
correct=[listing(100+i,'PlayStation 5 Slim Digital 825GB') for i in range(5)]
target=listing(1000,'PlayStation 5 Slim Digital 825GB')
from garimpei.infra.persistence.monitoring_models import MonitoringConfiguration,MonitoringInterest
from garimpei.infra.persistence.listing_models import ListingInterestMatch
from garimpei.infra.queries.assistance.postgres_queries import PostgresAssistanceQueries
configuration=MonitoringConfiguration.objects.filter(slot='active').first()
if configuration is None:
 configuration=MonitoringConfiguration.objects.create(id=UUID(int=2000),slot='active',revision=1,cep='01001000',resale_fee_percent=Decimal('10'),completed_at=now())
interest,_=MonitoringInterest.objects.get_or_create(configuration=configuration,kind='product',key='sony:ps5:slim:digital:825gb',defaults=dict(label='PlayStation 5 Slim Digital 825GB'))
ListingInterestMatch.objects.get_or_create(observation=target.latest,kind=interest.kind,key=interest.key)
selected=PostgresAssistanceRepository._candidates(target)
correct_ids={row.latest_id for row in correct}
assert correct_ids.issubset({row.id for row in selected}), 'irrelevant UUID prefix starved all five eligible equivalents'
assert selected[0].id in correct_ids, 'manual review selected unrelated first candidate'
seen=set()
for turn in range(7):
 chosen=PostgresAssistanceRepository._candidates(target)
 for candidate in chosen:
  if candidate.id in correct_ids: continue
  seen.add(candidate.id)
  snapshot=observation_snapshot(target,'comparables',candidate)
  AssistanceReview.objects.get_or_create(purpose='comparables',target_kind='listing_observation',target_id=target.latest_id,input_signature=digest(snapshot),defaults=dict(observation=target.latest,candidate_observation=candidate,generation=1,input_snapshot=json.loads(json.dumps(snapshot,default=str)),state='insufficient',result=dict(outcome='insufficient',findings=[],limitations=[])))
assert {row.latest_id for row in irrelevant}.issubset(seen), 'bounded exclusion reviews did not advance fairly'
coverage=next(row for row in PostgresAssistanceQueries().coverage()['rows'] if row['purpose']=='Comparáveis' and row['interest']==interest.label)
assert coverage['requested']>10, 'fixture must exercise more than a single admission turn'
assert coverage['denominator']==Listing.objects.exclude(latest=None).count()-1, 'denominator used admission budget instead of current pair universe'
assert coverage['requested']<=coverage['denominator']
"""

MANUAL = r"""
import json
from garimpei.domain.assistance.review import validate_assistance_output
from garimpei.domain.valuation.identity_ports import IdentityEdit
from garimpei.domain.valuation.product_catalog import product_values
from garimpei.infra.persistence.listing_models import ListingObservation
from tests.factories.assistance import seed_observation
from garimpei.infra.repository.valuation.identity_repository import PostgresIdentityRepository
from garimpei.infra.gateway.assistance.snapshots import observation_snapshot
from garimpei.infra.repository.valuation.identity_mapper import current_identification
from django.utils.timezone import now
identity,_=seed_observation('manual-regression','unicode')
observation=ListingObservation.objects.select_related('listing').get(pk=identity)
observation.evidence=dict(observation.evidence,title='PlayStation 5 Slim Digital 825GB',description='Usado. Funcionando perfeitamente.',condition='Usado — seminovo',source_available=True)
observation.save(update_fields=['evidence'])
repository=PostgresIdentityRepository(now)
values=tuple(sorted(product_values('sony:ps5:slim:digital:825gb').items()))
repository.save(IdentityEdit(observation.listing_id,1,0,'save',values,None))
row=observation.listing
row.refresh_from_db()
snapshot=observation_snapshot(row,'identity')
assert snapshot['facts'], 'manual identity discarded every original source reference'
assert snapshot['manual_revision']==1 and not snapshot['conflict']
fields={fact['field'] for fact in snapshot['facts']}
assert {'family','model','generation','edition','capacity'}.issubset(fields)
payload=dict(outcome='supported',findings=[dict(field=f['field'],value=f['value'],evidence_refs=[f['id']],reason_code='explicit_evidence') for f in snapshot['facts']],limitations=[])
assert validate_assistance_output('identity-review-v1',json.dumps(payload),json.dumps(snapshot,default=str))['outcome']=='supported'
assert all(fact['source']=='text' for fact in snapshot['facts'])
observation.evidence=dict(observation.evidence,title='PlayStation 5 Slim Digital 1TB');observation.save(update_fields=['evidence'])
row.refresh_from_db()
conflict=observation_snapshot(row,'identity')
assert conflict['conflict']
assert dict((a.name,a.value) for a in current_identification(row).attributes)['capacity']=='825gb'
from garimpei.infra.persistence.assistance_models import AssistanceReview
from garimpei.infra.gateway.assistance.snapshots import digest
from django.test import Client
AssistanceReview.objects.create(purpose='identity',target_kind='listing_observation',target_id=observation.id,observation=observation,generation=1,input_signature=digest(conflict),input_snapshot=json.loads(json.dumps(conflict,default=str)),state='conflict',result=dict(outcome='conflict',findings=[],limitations=[]))
response=Client(HTTP_HOST='localhost').get(f'/ofertas/{row.id}/ia/')
assert response.status_code==200
assert 'Correção manual preservada'.encode() in response.content,'manual value is hidden from the conflict review'
assert b'825 GB' in response.content and b'1TB' in response.content,'manual and observed values must both remain visible'
observation.evidence=dict(observation.evidence,title='PlayStation 5 Slim Digital');observation.save(update_fields=['evidence'])
row.refresh_from_db()
missing=observation_snapshot(row,'identity')
assert 'capacity' not in {f['field'] for f in missing['facts']}
assert 'capacity' in missing['required_fields'], 'missing source must not confirm a manual capacity'
"""


def test_candidate_limit_prioritizes_all_equivalents_and_rotates_exclusions(
    foundations: list[FoundationInstance],
) -> None:
    run_assert(foundations[0], SELECTION)


def test_manual_identity_preserves_source_support_conflict_and_unknown(
    foundations: list[FoundationInstance],
) -> None:
    run_assert(foundations[1], MANUAL)
