from uuid import uuid4

from garimpei.domain.robot.control import RobotStatus

TITLES = {
    "enabled": "Robô ligado",
    "draining": "Desligando",
    "disabled": "Robô desligado",
    "unknown": "Parada ainda não confirmada",
    "unavailable": "Estado do robô indisponível",
}


def robot_context(status: RobotStatus) -> dict[str, object]:
    return {
        "robot": status,
        "robot_title": TITLES[status.state],
        "robot_command_id": str(uuid4()),
        "robot_available": True,
    }
