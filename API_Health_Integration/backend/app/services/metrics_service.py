"""Metrics calculator.

N = S + E + T. Timeouts are failures. Latency uses successful requests only.
Rates are None (not 0) when there are no requests.
"""
from __future__ import annotations

import math
from collections import Counter

from app.domain import ERROR, SUCCESS, TIMEOUT, LogRecord
from app.schemas import FailureCount, IntegrationMetrics


def _pct(part: int, total: int) -> float | None:
    return None if total == 0 else 100.0 * part / total


def nearest_rank_percentile(values: list[float], pct: float) -> float | None:
    """Nearest-rank percentile: the smallest value >= pct% of the data.

    With 12 samples, p95 = rank ceil(11.4) = 12 = the maximum. Documented.
    """
    if not values:
        return None
    ordered = sorted(values)
    rank = max(1, math.ceil(pct / 100.0 * len(ordered)))
    return ordered[rank - 1]


def compute_metrics(logs: list[LogRecord]) -> IntegrationMetrics:
    total = len(logs)
    successes = sum(1 for r in logs if r.status == SUCCESS)
    errors = sum(1 for r in logs if r.status == ERROR)
    timeouts = sum(1 for r in logs if r.status == TIMEOUT)
    success_latencies = [r.latency_ms for r in logs if r.status == SUCCESS]

    failure_counter = Counter(r.failure_key for r in logs if r.failure_key is not None)
    # Deterministic order: most frequent first, ties broken alphabetically.
    failure_counts = [
        FailureCount(failure=k, count=v)
        for k, v in sorted(failure_counter.items(), key=lambda kv: (-kv[1], kv[0]))
    ]

    success_times = [r.timestamp for r in logs if r.status == SUCCESS]
    return IntegrationMetrics(
        total_requests=total,
        successes=successes,
        errors=errors,
        timeouts=timeouts,
        success_rate=_pct(successes, total),
        error_rate=_pct(errors, total),
        timeout_rate=_pct(timeouts, total),
        failure_rate=_pct(errors + timeouts, total),
        avg_latency_ms=(sum(success_latencies) / len(success_latencies)) if success_latencies else None,
        p95_latency_ms=nearest_rank_percentile(success_latencies, 95),
        last_success=max(success_times) if success_times else None,
        last_seen=max((r.timestamp for r in logs), default=None),
        failure_counts=failure_counts,
    )
