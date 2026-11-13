from typing import cast
from uuid import UUID

from django import forms
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from garimpei.domain.robot.control import RobotCommand
from garimpei.domain.robot.errors import RobotError
from garimpei.infra.http.robot.presentation import robot_context
from garimpei.usecase.robot.read_robot_status_usecase import ReadRobotStatusUseCase
from garimpei.usecase.robot.set_robot_state_usecase import SetRobotStateUseCase


class RobotCommandForm(forms.Form):
    revision = forms.IntegerField(min_value=0, max_value=9999999999999999)
    command_id = forms.UUIDField()


class RobotHandler:
    def __init__(self, read: ReadRobotStatusUseCase, command: SetRobotStateUseCase) -> None:
        self._read, self._command = read, command

    def handle(self, request: HttpRequest, action: str = "status") -> HttpResponse:
        allowed = "GET" if action == "status" else "POST"
        if request.method != allowed:
            return HttpResponse(status=405, headers={"Allow": allowed})
        if action == "status":
            response = render(request, "robot/control.html", robot_context(self._read.execute()))
            response["Cache-Control"] = "no-store"
            return response
        form = RobotCommandForm(request.POST)
        if not form.is_valid():
            raise RobotError(
                "invalid_robot_command",
                "Comando inválido: esperado revision inteiro não negativo e command_id UUID.",
                400,
            )
        self._command.execute(
            RobotCommand(
                cast(UUID, form.cleaned_data["command_id"]),
                action == "enable",
                int(form.cleaned_data["revision"]),
            )
        )
        return HttpResponse(
            status=303, headers={"Location": "/acompanhamento/", "Cache-Control": "no-store"}
        )
