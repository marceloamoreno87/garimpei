"""Operational engineering profile, distinguished from measured observations."""

PROFILE: dict[str, int] = {
    "version": 1,
    "stalled_seconds": 180,
    "tick_seconds": 5,
    "failures": 3,
    "queue_limit": 1000,
    "unit_seconds": 60,
    "archive_seconds": 300,
    "data_bytes": 10 * 1024**3,
    "backup_bytes": 10 * 1024**3,
    "reserve_bytes": 1024**3,
    "backup_interval": 86400,
    "retention": 7,
}
