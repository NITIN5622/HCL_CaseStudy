"""Failure analyzer: dominant failure pattern + recommendations."""
from __future__ import annotations

from app.schemas import IntegrationMetrics, Recommendation, RuleResult
from app.services.recommendation_engine import recommend


def dominant_failure(metrics: IntegrationMetrics) -> str | None:
    # failure_counts is already sorted by (-count, name): deterministic tie-break.
    return metrics.failure_counts[0].failure if metrics.failure_counts else None


def analyze(metrics: IntegrationMetrics, rules: list[RuleResult]) -> list[Recommendation]:
    recs: list[Recommendation] = []

    for fc in metrics.failure_counts:
        cause, step = recommend(fc.failure)
        recs.append(Recommendation(signal=fc.failure, count=fc.count, possible_cause=cause, next_step=step))

    latency_rule = next((r for r in rules if r.rule == "avg_latency_ms"), None)
    if latency_rule and latency_rule.severity in ("degraded", "critical"):
        cause, step = recommend("high_latency")
        recs.append(Recommendation(signal="high_latency", count=metrics.successes, possible_cause=cause, next_step=step))

    if metrics.total_requests == 0:
        cause, step = recommend("no_data")
        recs.append(Recommendation(signal="no_data", count=0, possible_cause=cause, next_step=step))

    return recs
