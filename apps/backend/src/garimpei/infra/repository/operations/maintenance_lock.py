from collections.abc import Iterator
from contextlib import contextmanager

from django.db import connection

from garimpei.domain.operations.errors import OperationsError


@contextmanager
def maintenance_lock() -> Iterator[None]:
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_try_advisory_lock(73417)")
        acquired = cursor.fetchone()
    if acquired is None or acquired[0] is not True:
        raise OperationsError("maintenance_in_progress")
    try:
        yield
    finally:
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_unlock(73417)")
