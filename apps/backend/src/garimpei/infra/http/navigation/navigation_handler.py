import re
from uuid import UUID

from django.http import HttpRequest, HttpResponse, HttpResponseNotAllowed
from django.shortcuts import render

from garimpei.domain.navigation.ports import InvalidNavigation
from garimpei.usecase.navigation.read_status_usecase import ReadNavigationStatusUseCase
from garimpei.usecase.navigation.read_suggestions_usecase import ReadSuggestionsUseCase
from garimpei.usecase.navigation.resume_work_usecase import ResumeWorkUseCase


def parse_identity(value: str) -> UUID:
    if not re.fullmatch(r"[a-fA-F0-9]{8}(?:-[a-fA-F0-9]{4}){3}-[a-fA-F0-9]{12}", value):
        raise InvalidNavigation
    return UUID(value)


class NavigationHandler:
    def __init__(
        self,
        status: ReadNavigationStatusUseCase,
        suggestions: ReadSuggestionsUseCase,
        resume: ResumeWorkUseCase,
    ) -> None:
        self._status, self._suggestions, self._resume = status, suggestions, resume

    def handle(self, request: HttpRequest, action: str = "status") -> HttpResponse:
        methods = ["POST"] if action == "resume" else ["GET"]
        if request.method not in methods:
            return HttpResponseNotAllowed(methods)
        if action == "resume":
            identity = parse_identity(request.POST.get("work_id", ""))
            revision = request.POST.get("revision", "")
            if not re.fullmatch(r"[1-9][0-9]{0,17}", revision):
                raise InvalidNavigation
            self._resume.execute(identity, int(revision))
            return HttpResponse(
                status=303, headers={"Location": "/acompanhamento/", "Cache-Control": "no-store"}
            )
        if action == "suggestions":
            page = request.GET.get("pagina", "1")
            if not re.fullmatch(r"[1-9][0-9]{0,8}", page):
                raise InvalidNavigation
            return render(
                request,
                "navigation/suggestions.html",
                {"suggestions": self._suggestions.execute(int(page))},
            )
        return render(request, "navigation/progress.html", {"navigation": self._status.execute()})
