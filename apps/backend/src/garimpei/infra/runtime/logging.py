import json
import logging
import re
import traceback
from datetime import UTC, datetime
from io import TextIOBase
from pathlib import Path

from garimpei.config.env import logging_context


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        environment_id, run_id = logging_context()
        # Third-party exception text/arguments can contain DSNs or headers.
        data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": getattr(record, "event", "runtime_event"),
            "environment_id": environment_id,
            "run_id": run_id,
        }
        code = getattr(record, "error_code", None)
        if isinstance(code, str) and re.fullmatch(r"[A-Z][A-Z0-9_]{1,63}", code):
            data["error_code"] = code
        elif record.exc_info or record.levelno >= logging.ERROR:
            data["error_code"] = "RUNTIME_ERROR"
        if record.exc_info and record.exc_info[0] is not None:
            data["error_type"] = record.exc_info[0].__name__
            data["error_frames"] = [
                {"file": Path(frame.filename).name, "line": frame.lineno, "function": frame.name}
                for frame in traceback.extract_tb(record.exc_info[2])[-5:]
            ]
        if data["event"] == "profit_read_failed":
            data["profit_identity"] = getattr(record, "profit_identity", None)
        if data["event"] == "collection_finished":
            for field in (
                "collection_cycle",
                "collection_revision",
                "collection_phase",
                "collection_reasons",
                "collection_observations",
            ):
                data[field] = getattr(record, field, None)
        if data["event"] == "collection_source_page":
            for field in (
                "source_query",
                "source_page",
                "source_count",
                "source_first_publication",
                "source_last_publication",
                "source_has_next",
                "source_main_results_ended",
                "source_window_proof",
                "source_ordered",
                "source_native_sort",
                "source_geography_verified",
                "source_radius_km",
            ):
                data[field] = getattr(record, field, None)
        if data["event"] == "alert_state":
            for field in ("alert_reference", "alert_state", "alert_reason"):
                data[field] = getattr(record, field, None)
        return json.dumps(data)


class WorkerNoticeStream(TextIOBase):
    """Normalize official CLI notices; handlers keep their original stderr."""

    def write(self, text: str) -> int:
        if text.strip():
            logging.getLogger("garimpei.worker").info(
                "worker_cli_notice", extra={"event": "worker_cli_notice"}
            )
        return len(text)
