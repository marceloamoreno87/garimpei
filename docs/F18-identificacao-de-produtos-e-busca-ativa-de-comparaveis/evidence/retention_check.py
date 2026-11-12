from pathlib import Path
import sys
root=Path(__file__).resolve().parents[3];sys.path.insert(0,str(root/'apps/backend'))
from tests.factories.runtime import FoundationInstance,pause_worker,resume_worker
from tests.integration.test_collection import shell
instance=FoundationInstance(root,Path((root/'.runtime/f18-execution/envfile-path.txt').read_text().strip()))
worker=pause_worker(instance)
try:
 shell(instance,"""
from datetime import timedelta
from dataclasses import replace
from decimal import Decimal
from django.utils.timezone import now
from garimpei.main import build_read_valuation,build_read_profit,build_read_monitoring_configuration
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.persistence.research_models import ComparableInvestigation,ResearchCandidateDecision
from garimpei.infra.persistence.valuation_models import ValuationEvaluation
from garimpei.infra.repository.valuation.research_repository import PostgresComparableResearchRepository
from garimpei.infra.repository.listing.postgres_repository import PostgresCollectionRepository
from garimpei.domain.listing.ports import SourceFailure
from tests.factories.comparable_research import controlled_limits
from garimpei.infra.queries.valuation.postgres_queries import PostgresValuationQueries
from garimpei.usecase.valuation.read_valuation_usecase import ReadValuationUseCase
from garimpei.usecase.valuation.read_profit_usecase import ReadProfitUseCase
l=Listing.objects.get(external_id='18901');before=build_read_valuation().execute(l.id)
assert before.resale.price==Decimal('2300') and len(before.resale.comparables)==5
edge=before.resale.valid_until;assert edge is not None
configuration=build_read_monitoring_configuration();at=now()
repo=PostgresComparableResearchRepository(configuration,lambda:at,controlled_limits(),PostgresCollectionRepository(configuration,lambda:at,lambda *_:0,40))
repo.reconcile();row=ComparableInvestigation.objects.get(product_key=before.product)
query=row.queries.get();assert query.term and query.requested['radius_km']==500 and query.observed['verified']
decisions=list(ResearchCandidateDecision.objects.filter(query=query));assert len(decisions)>=5
required={'source','external_id','url','price','source_available','observed_at','revision','price_kind'}
assert all(required<=set(d.evidence) for d in decisions)
assert all(d.evidence.get('selection_history') for d in decisions)
history=ValuationEvaluation.objects.count();confirmed=row.details
row.state='waiting_evidence';row.next_attempt_at=at;row.lease_until=None;row.save()
work=repo.claim();assert work is not None
repo.failed(work,SourceFailure('source_http_503'));row.refresh_from_db()
assert row.state=='waiting_retry' and row.reason=='source_http_503' and row.details==confirmed
read=PostgresValuationQueries()
assert read.current(l.id,at).resale.price==Decimal('2300')
assert read.current(l.id,edge).resale.price==Decimal('2300')
after=read.current(l.id,edge+timedelta(seconds=1));assert after.resale.price is None and after.resale.reason=='evidencia_vencida'
profit=build_read_profit();expired=ReadProfitUseCase(profit._reader,lambda:edge+timedelta(seconds=1)).execute(l.id)
assert expired.resale.value is None and expired.profit.value is None
assert read.historical(before.id).resale.price==Decimal('2300')
assert ValuationEvaluation.objects.count()==history and row.queries.count()==1 and row.details==5
""")
 print('RETENTION_PASS source503 waitingretry;2300 before/exactedge;expiredresale/profitNone;historical2300/queries/details retained; sourceprovenanceandselectionhistory complete')
finally: resume_worker(worker)
