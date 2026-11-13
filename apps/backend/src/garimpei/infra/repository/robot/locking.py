"""The first lock in every operational admission/publication transaction."""

from django.db import connection


def lock_robot_control() -> None:
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(73000)")
