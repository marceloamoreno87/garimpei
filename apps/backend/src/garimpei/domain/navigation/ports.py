from collections.abc import Callable
from typing import Protocol
from uuid import UUID

from garimpei.domain.listing.listing import Candidate
from garimpei.domain.listing.ports import Attempt, Page, SourceFailure
from garimpei.domain.listing.scope import Scope
from garimpei.domain.navigation.work import NavigationUnit

type Monotonic = Callable[[], float]


class NavigationStore(Protocol):
    def prepare(self, attempt: Attempt, scope: Scope) -> None: ...
    def claim(
        self, attempt: Attempt, scope: Scope, *, pages: int, details: bool
    ) -> NavigationUnit | None: ...
    def page(self, attempt: Attempt, unit: NavigationUnit, page: Page) -> None: ...
    def detail(self, attempt: Attempt, unit: NavigationUnit, candidate: Candidate) -> None: ...
    def failed(self, attempt: Attempt, unit: NavigationUnit, failure: SourceFailure) -> bool: ...
    def yield_slice(self, attempt: Attempt, scope: Scope) -> None: ...
    def resume(self, identity: UUID, revision: int) -> None: ...
    def request_research(
        self,
        request_id: UUID,
        revision: int,
        interest: str,
        term: str,
        purpose: str,
        constraints: str,
    ) -> UUID: ...


class NavigationError(Exception):
    status = 503
    message = "Não foi possível ler ou gravar o percurso. Tente novamente."


class InvalidNavigation(NavigationError):
    status = 400
    message = "Entrada inválida: use UUID de trabalho e revisão inteira positiva."


class MissingNavigation(NavigationError):
    status = 404
    message = "Trabalho ou sugestão indisponível para os interesses atuais."


class StaleNavigation(NavigationError):
    status = 409
    message = "A revisão mudou ou o acesso está suspenso. Confira a conexão e recarregue."


class NavigationQueries(Protocol):
    def status(self) -> "NavigationStatus": ...
    def research(self, identity: UUID) -> "ResearchStatus": ...
    def suggestions(self, page: int) -> "SuggestionPage": ...
    def suggestion(self, identity: UUID) -> "SuggestionView": ...


from garimpei.domain.navigation.read_models import (  # noqa: E402
    NavigationStatus,
    ResearchStatus,
    SuggestionPage,
    SuggestionView,
)


class SuggestionStore(Protocol):
    def claim(self) -> "SuggestionUnit | None": ...
    def page(self, unit: "SuggestionUnit", page: Page) -> str | None: ...
    def confirm(self, unit: "SuggestionUnit", candidate: Candidate) -> None: ...
    def failed(self, unit: "SuggestionUnit", failure: SourceFailure) -> None: ...


from garimpei.domain.navigation.work import SuggestionUnit  # noqa: E402
