import json
import logging

from garimpei.infra.runtime.logging import JsonFormatter


def test_raw_exception_and_message_never_cross_log_boundary() -> None:
    canary = "private-log-canary"
    record = logging.LogRecord("test", logging.ERROR, __file__, 1, canary, (), None)
    encoded = JsonFormatter().format(record)
    data = json.loads(encoded)
    assert canary not in encoded
    assert {
        "timestamp",
        "level",
        "logger",
        "event",
        "environment_id",
        "run_id",
        "error_code",
    } <= data.keys()


def test_configuration_warning_preserves_code_without_form_content() -> None:
    record = logging.LogRecord(
        "garimpei.http", logging.WARNING, __file__, 1, "private-form-input", (), None
    )
    setattr(record, "error_code", "CONFIGURATION_CONFLICT")
    encoded = JsonFormatter().format(record)
    assert json.loads(encoded)["error_code"] == "CONFIGURATION_CONFLICT"
    assert "private-form-input" not in encoded


def test_exception_location_is_available_without_exception_text_or_locals() -> None:
    import sys

    try:
        raise RuntimeError("private-exception-arguments")
    except RuntimeError:
        record = logging.LogRecord(
            "test", logging.ERROR, __file__, 1, "private-message", (), sys.exc_info()
        )
    raw = JsonFormatter().format(record)
    data = json.loads(raw)
    assert data["error_type"] == "RuntimeError"
    assert (
        data["error_frames"][-1]["function"]
        == "test_exception_location_is_available_without_exception_text_or_locals"
    )
    assert "private-exception-arguments" not in raw and "private-message" not in raw
