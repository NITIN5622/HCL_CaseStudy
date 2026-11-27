"""Time-bucketed request status and latency, for the details-page charts."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.domain import ERROR, SUCCESS, TIMEOUT, LogRecord
from app.schemas import TrendBucket, Trends, WindowInfo

# Pick the smallest bucket that keeps the chart at <= ~48 bars.
_NICE_MINUTES = [5, 10, 15, 30, 60, 120, 360, 720, 1440]
_MAX_BUCKETS = 48
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def _bucket_minutes(span: timedelta) -> int:
    minutes = span.total_seconds() / 60
    for m in _NICE_MINUTES:
        if minutes / m <= _MAX_BUCKETS:
            return m
    return _NICE_MINUTES[-1]


def _floor(ts: datetime, minutes: int) -> datetime:
    step = minutes * 60
    seconds = int((ts - _EPOCH).total_seconds())
    return _EPOCH + timedelta(seconds=seconds - seconds % step)


def build_trends(logs: list[LogRecord], win: WindowInfo) -> Trends:
    if win.end is None:
        return Trends(bucket_minutes=5, buckets=[])

    # Bucket size follows the selected window; the axis starts at the first log.
    minutes = _bucket_minutes(win.end - (win.start or (logs[0].timestamp if logs else win.end)))
    first = logs[0].timestamp if logs else (win.start or win.end)
    step = timedelta(minutes=minutes)

    # Empty buckets are kept so gaps in traffic are visible on the chart.
    buckets: dict[datetime, list[LogRecord]] = {}
    cursor = _floor(first, minutes)
    while cursor <= win.end:
        buckets[cursor] = []
        cursor += step
    for r in logs:
        buckets.setdefault(_floor(r.timestamp, minutes), []).append(r)

    out = []
    for start in sorted(buckets):
        rs = buckets[start]
        lat = [r.latency_ms for r in rs if r.status == SUCCESS]
        out.append(TrendBucket(
            start=start,
            success=sum(r.status == SUCCESS for r in rs),
            error=sum(r.status == ERROR for r in rs),
            timeout=sum(r.status == TIMEOUT for r in rs),
            avg_latency_ms=(sum(lat) / len(lat)) if lat else None,
        ))
    return Trends(bucket_minutes=minutes, buckets=out)
