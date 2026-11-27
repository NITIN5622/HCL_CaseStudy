from datetime import datetime, timedelta, timezone

import pytest

from app.domain import LogRecord
from app.services.metrics_service import compute_metrics, nearest_rank_percentile

T0 = datetime(2026, 8, 4, 9, 0, tzinfo=timezone.utc)


def rec(status, code=200, latency=100, minute=0, name="X"):
    return LogRecord(
        integration=name, timestamp=T0 + timedelta(minutes=minute), status=status,
        status_code=code, latency_ms=latency, fingerprint=f"{status}{minute}{latency}",
        source="test", ingested_at=T0,
    )


def test_timeouts_count_as_failures_greenhouse_case():
    # Greenhouse shape: 6 success, 1 error, 5 timeouts.
    logs = (
        [rec("success", minute=i) for i in range(6)]
        + [rec("error", code=500, minute=6)]
        + [rec("timeout", code=None, latency=30000, minute=7 + i) for i in range(5)]
    )
    m = compute_metrics(logs)
    assert (m.total_requests, m.successes, m.errors, m.timeouts) == (12, 6, 1, 5)
    assert m.failure_rate == pytest.approx(50.0)          # starter code says 14.29%
    assert m.error_rate == pytest.approx(100 / 12)
    assert m.timeout_rate == pytest.approx(500 / 12)
    assert m.avg_latency_ms == 100                         # 30 s timeouts excluded
    assert m.failure_counts[0].failure == "timeout"


def test_no_logs_gives_null_rates_not_zero():
    m = compute_metrics([])
    assert m.total_requests == 0
    assert m.failure_rate is None and m.error_rate is None and m.timeout_rate is None
    assert m.avg_latency_ms is None and m.p95_latency_ms is None and m.last_success is None


def test_all_failures_gives_null_latency():
    m = compute_metrics([rec("error", code=500, minute=i) for i in range(5)])
    assert m.failure_rate == 100.0
    assert m.avg_latency_ms is None and m.last_success is None


def test_nearest_rank_p95():
    assert nearest_rank_percentile(list(range(1, 13)), 95) == 12   # 12 samples -> max
    assert nearest_rank_percentile(list(range(1, 101)), 95) == 95
    assert nearest_rank_percentile([], 95) is None


def test_failure_tie_break_is_deterministic():
    logs = [rec("error", code=503, minute=0), rec("error", code=500, minute=1)]
    m = compute_metrics(logs)
    assert [f.failure for f in m.failure_counts] == ["HTTP 500", "HTTP 503"]
