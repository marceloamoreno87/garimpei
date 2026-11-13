from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest

from garimpei.domain.robot.errors import RobotUnavailable
from garimpei.infra.http.robot.presentation import robot_context
from garimpei.main import build_read_robot_status


def robot_summary(request: HttpRequest) -> dict[str, object]:
    if request.path != "/acompanhamento/" and not request.path.startswith("/ofertas/"):
        return {}
    try:
        return robot_context(build_read_robot_status().execute())
    except (RobotUnavailable, ImproperlyConfigured):
        return {"robot_available": False, "robot_title": "Estado do robô indisponível"}
