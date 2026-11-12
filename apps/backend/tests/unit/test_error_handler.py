import json
import logging

from django.http import HttpResponse
from django.test import RequestFactory

from garimpei.infra.http.error_handler import ErrorMiddleware


def test_unexpected_http_error_has_no_private_exception_text() -> None:
    request = RequestFactory().get("/health")
    response = ErrorMiddleware(lambda _: HttpResponse()).process_exception(
        request, RuntimeError("private-header-canary")
    )
    assert response is not None
    assert response.status_code == 500
    assert json.loads(response.content) == {"error": {"code": "INTERNAL_ERROR"}}
    assert b"private-header-canary" not in response.content


def test_library_error_record_never_serializes_exception() -> None:
    from garimpei.infra.runtime.logging import JsonFormatter

    try:
        raise RuntimeError("private-exception-canary")
    except RuntimeError as error:
        record = logging.LogRecord(
            "library",
            logging.ERROR,
            __file__,
            1,
            str(error),
            (),
            (type(error), error, error.__traceback__),
        )
    assert "private-exception-canary" not in JsonFormatter().format(record)
