from datetime import datetime
from uuid import UUID

from django.db.models import QuerySet, Sum

from garimpei.domain.listing.ports import Clock, ConfigurationReader
from garimpei.domain.listing.scope import Scope
from garimpei.domain.navigation.policy import (
    NavigationPolicy,
    decide_suggestion,
    suggestion_capacity,
)
from garimpei.domain.navigation.ports import MissingNavigation, NavigationError
from garimpei.domain.navigation.read_models import (
    EvidenceView,
    NavigationStatus,
    ResearchLimits,
    ResearchStatus,
    SuggestionBudget,
    SuggestionPage,
    SuggestionView,
    WorkView,
)
from garimpei.infra.persistence.listing_models import (
    CollectionCandidate,
    CollectionState,
    ListingObservation,
)
from garimpei.infra.persistence.navigation_models import (
    NavigationCheckpoint,
    NavigationWork,
    NicheSuggestion,
)


class PostgresNavigationQueries:
    def __init__(
        self,
        configuration: ConfigurationReader,
        clock: Clock,
        policy: NavigationPolicy,
        timeout: int,
        cadence: float,
    ) -> None:
        self._configuration, self._clock = configuration, clock
        self._policy = policy
        self._timeout, self._cadence = timeout, cadence

    def status(self) -> NavigationStatus:
        scope = Scope.from_snapshot(self._configuration.execute())
        if scope is None:
            return NavigationStatus(
                self._clock(), (), self._policy.cycle_pages, self._policy.cycle_terms
            )
        records = NavigationWork.objects.filter(
            configuration_id=scope.configuration_id,
            revision=scope.revision,
            cycle__state__current_id__isnull=False,
        ).order_by("-cycle__started_at", "origin_interest", "front")
        works = []
        page_limit, term_limit = self._policy.cycle_pages, self._policy.cycle_terms
        for row in records:
            if row.cycle.state.current_id != row.cycle_id:
                continue
            checkpoint = NavigationCheckpoint.objects.get(work=row)
            page_limit = int(checkpoint.limits.get("cycle_pages", page_limit))
            term_limit = int(checkpoint.limits.get("cycle_terms", term_limit))
            pending = CollectionCandidate.objects.filter(
                cycle_id=row.cycle_id, query_key=row.origin_interest
            ).count()
            original = next(
                (query.term for query in scope.searches if query.key == row.origin_interest),
                row.original_term,
            )
            observations = self._observations(row) if row.purpose == "research" else ()
            works.append(
                WorkView(
                    row.id,
                    row.revision,
                    original,
                    row.front,
                    checkpoint.terms[checkpoint.term_index],
                    original,
                    checkpoint.catalog_version,
                    row.phase,
                    row.reason,
                    row.last_progress_at,
                    row.next_attempt_at,
                    checkpoint.pages,
                    checkpoint.details,
                    pending,
                    len(checkpoint.buffered_candidates),
                    row.purpose,
                    observations,
                )
            )
        return NavigationStatus(self._clock(), tuple(works), page_limit, term_limit)

    def research(self, identity: UUID) -> ResearchStatus:
        row = (
            NavigationWork.objects.select_related("cycle__state")
            .filter(id=identity, purpose="research", request_id__isnull=False)
            .first()
        )
        if row is None:
            raise MissingNavigation
        checkpoint = NavigationCheckpoint.objects.get(work=row)
        snapshot = self._configuration.execute()
        limits = self._research_limits(checkpoint)
        shared = (
            NavigationCheckpoint.objects.filter(
                work__cycle=row.cycle,
                work__origin_interest=row.origin_interest,
                work__front="discovery",
            ).aggregate(pages=Sum("pages"))["pages"]
            or 0
        )
        historical = (
            row.cycle.finished_at is not None
            or row.cycle.state.current_id != row.cycle_id
            or snapshot.revision != row.revision
            or snapshot.configuration_id != row.configuration_id
        )
        return ResearchStatus(
            row.id,
            row.revision,
            row.source,
            row.origin_interest,
            row.original_term,
            str(checkpoint.context.get("purpose", "research")),
            row.phase,
            row.reason,
            row.scope_key,
            checkpoint.context_hash,
            self._window_time(checkpoint.context.get("window_start")),
            self._window_time(checkpoint.context.get("window_end")),
            limits,
            checkpoint.pages,
            checkpoint.details,
            int(shared),
            self._observations(row),
            historical,
        )

    @staticmethod
    def _research_limits(checkpoint: NavigationCheckpoint) -> ResearchLimits:
        pages, terms = checkpoint.limits.get("cycle_pages"), checkpoint.limits.get("cycle_terms")
        if (
            not isinstance(pages, int)
            or not isinstance(terms, int)
            or pages < 1
            or not 1 <= terms <= 3
        ):
            raise NavigationError
        return ResearchLimits(pages, terms)

    @staticmethod
    def _window_time(value: object) -> datetime | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise NavigationError
        try:
            stamp = datetime.fromisoformat(value)
        except ValueError:
            raise NavigationError from None
        if stamp.tzinfo is None:
            raise NavigationError
        return stamp

    def _observations(self, row: NavigationWork) -> tuple[UUID, ...]:
        kind, key = row.origin_interest.removeprefix("marketplace:").split(":", 1)
        return tuple(
            ListingObservation.objects.filter(cycle=row.cycle, matches__kind=kind, matches__key=key)
            .values_list("id", flat=True)
            .distinct()
        )

    def _suggestions(self) -> QuerySet[NicheSuggestion]:
        snapshot = self._configuration.execute()
        if snapshot.configuration_id is None or snapshot.revision is None:
            return NicheSuggestion.objects.none()
        return NicheSuggestion.objects.filter(
            configuration_id=snapshot.configuration_id,
            revision=snapshot.revision,
            state__in=["supported", "limited"],
            observed_at__isnull=False,
        ).order_by("-observed_at", "id")

    def suggestions(self, page: int) -> SuggestionPage:
        rows = list(self._suggestions()[(page - 1) * 20 : page * 20 + 1])
        return SuggestionPage(
            tuple(self._view(row) for row in rows[:20]), page, len(rows) > 20, self._budget()
        )

    def _budget(self) -> SuggestionBudget:
        snapshot, now = self._configuration.execute(), self._clock()
        configured = snapshot.configured and snapshot.configuration_id is not None
        identity = snapshot.configuration_id
        records = (
            NicheSuggestion.objects.filter(configuration_id=identity)
            if configured and identity is not None
            else NicheSuggestion.objects.none()
        )
        latest = records.exclude(last_slice_at=None).order_by("-last_slice_at").first()
        state = (
            CollectionState.objects.filter(
                configuration_id=identity, source=snapshot.source
            ).first()
            if configured and identity is not None
            else None
        )
        admission = decide_suggestion(
            self._policy,
            now,
            configured=configured,
            initialized=state is not None,
            active_ready=bool(state and state.current and state.current.finished_at is None),
            active_due=state.next_attempt_at if state else None,
            last_slice=latest.last_slice_at if latest else None,
            timeout=self._timeout,
            cadence=self._cadence,
            source_until=state.source_not_before if state else None,
            suspended=bool(state and state.access_suspended),
        )
        messages = {
            "not_configured": "Conclua a configuração para explorar nichos relacionados.",
            "initial_collection": "As sugestões começam após a primeira coleta dos interesses salvos.",
            "access_suspended": "O acesso à fonte precisa de confirmação manual. As evidências salvas continuam disponíveis.",
            "source_wait": "A fonte pediu uma pausa. Sugestões aguardam o prazo confirmado.",
            "active_work": "Interesses ativos têm prioridade. Sugestões aguardam tempo livre.",
            "active_due_soon": "A próxima coleta está próxima. Não há tempo para outra operação de sugestões.",
            "cooldown": "Aguardando o intervalo entre explorações. Reiniciar não repõe o orçamento.",
            "budget_too_short": "O orçamento de tempo não comporta uma operação. Revise os limites de navegação.",
            "idle_available": "Há tempo livre para explorar relações verificadas, mantendo os interesses ativos como prioridade.",
        }
        capacity = suggestion_capacity(
            self._policy, new_suggestion=True, suggestion_count=records.count(), evidence_count=0
        )
        capacity_message = (
            "Limite de registros atingido. Novas sugestões aguardam; evidências existentes são preservadas."
            if capacity
            else ""
        )
        return SuggestionBudget(
            admission.reason,
            messages[admission.reason],
            admission.next_at,
            latest.pages if latest else 0,
            latest.details if latest else 0,
            self._policy.suggestion_pages,
            self._policy.suggestion_details,
            self._policy.suggestion_seconds,
            self._policy.suggestion_interval,
            records.count(),
            self._policy.suggestion_limit,
            self._policy.evidence_limit,
            capacity,
            capacity_message,
        )

    def suggestion(self, identity: UUID) -> SuggestionView:
        row = self._suggestions().filter(id=identity).first()
        if row is None:
            raise MissingNavigation
        return self._view(row)

    def _view(self, row: NicheSuggestion) -> SuggestionView:
        assert row.observed_at is not None
        evidence = tuple(
            EvidenceView(
                item.canonical_url, item.excerpt, item.observed_at, item.source, item.external_id
            )
            for item in row.evidence.order_by("-observed_at", "external_id")
        )
        return SuggestionView(
            row.id,
            row.term,
            row.original_term,
            row.relation_reason,
            row.observed_at,
            evidence,
            row.revision,
            suggestion_capacity(
                self._policy, new_suggestion=False, suggestion_count=0, evidence_count=len(evidence)
            ),
        )
