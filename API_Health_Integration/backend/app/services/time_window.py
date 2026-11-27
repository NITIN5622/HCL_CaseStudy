"""Time-window resolution, including historical demo mode.

The sample logs are from 2026-08-04. With the real clock, "last 1h" would be
empty, so in demo mode the reference time ("now") is the latest stored log.
Window semantics: start < timestamp <= end.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.repositories.log_repository import LogRepository
from app.schemas import WindowInfo

WINDOWS: dict[str, timedelta | None] = {
    "15m": timedelta(minutes=15),
    "30m": timedelta(minutes=30),
    "1h": timedelta(hours=1),
    "6h": timedelta(hours=6),
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "all": None,
}


class InvalidWindowError(ValueError):
    pass


def resolve_window(window: str, repo: LogRepository, demo_mode: bool, file_id: str | None = None) -> WindowInfo:
    if window not in WINDOWS:
        raise InvalidWindowError(f"window must be one of: {', '.join(WINDOWS)}")

    earliest, latest = repo.time_range()
    if demo_mode:
        mode = "historical"
        end = latest  # None when the store is empty
    else:
        mode = "live"
        end = datetime.now(timezone.utc)

    span = WINDOWS[window]
    start = None if (span is None or end is None) else end - span
    return WindowInfo(
        file_id=file_id,
        mode=mode, window=window, start=start, end=end,
        data_earliest=earliest, data_latest=latest,
    )
