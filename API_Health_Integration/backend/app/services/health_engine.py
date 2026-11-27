"""Health rule engine.

    if N < minimum_requests        -> UNKNOWN
    elif any rule is critical      -> CRITICAL
    elif any rule is degraded      -> DEGRADED
    else                           -> HEALTHY

Every rule is evaluated and returned (not just the first hit) so the UI can
show exactly why a status was assigned. Comparisons use unrounded values.
"""
from __future__ import annotations

from app.config import HealthPolicy, IntegrationSettings
from app.domain import CRITICAL, DEGRADED, HEALTHY, UNKNOWN
from app.schemas import IntegrationMetrics, RuleResult


def _grade(value: float | None, degraded: float, critical: float) -> str:
    if value is None:
        return "skipped"
    if value >= critical:
        return "critical"
    if value >= degraded:
        return "degraded"
    return "ok"


def _fmt(value: float | None, unit: str) -> str:
    if value is None:
        return "n/a"
    if unit == "%":
        return f"{value:.2f}%"
    return f"{int(value + 0.5)} ms"  # round half up, same as the UI (198.5 -> 199)


def _rule(name: str, label: str, value: float | None, degraded: float, critical: float, unit: str) -> RuleResult:
    severity = _grade(value, degraded, critical)
    v = _fmt(value, unit)
    if severity == "skipped":
        message = f"{label}: no data to evaluate"
    elif severity == "critical":
        message = f"{label} {v} >= {_fmt(critical, unit)} (critical)"
    elif severity == "degraded":
        message = f"{label} {v} >= {_fmt(degraded, unit)} (degraded)"
    else:
        message = f"{label} {v} < {_fmt(degraded, unit)} (ok)"
    return RuleResult(
        rule=name,
        value=value,
        degraded_threshold=degraded,
        critical_threshold=critical,
        severity=severity,
        message=message,
    )


def evaluate(
    metrics: IntegrationMetrics,
    policy: HealthPolicy,
    settings: IntegrationSettings,
) -> tuple[str, list[RuleResult]]:
    slo = settings.latency_slo_ms
    rules = [
        _rule("failure_rate", "Failure rate", metrics.failure_rate,
              policy.failure_degraded, policy.failure_critical, "%"),
        _rule("timeout_rate", "Timeout rate", metrics.timeout_rate,
              policy.timeout_degraded, policy.timeout_critical, "%"),
        _rule("avg_latency_ms", "Avg success latency", metrics.avg_latency_ms,
              slo, slo * policy.latency_critical_multiplier, "ms"),
    ]

    if metrics.total_requests < policy.minimum_requests:
        sample_rule = RuleResult(
            rule="minimum_requests",
            value=float(metrics.total_requests),
            degraded_threshold=float(policy.minimum_requests),
            critical_threshold=float(policy.minimum_requests),
            severity="skipped",
            message=(
                f"Only {metrics.total_requests} request(s) in window; "
                f"need >= {policy.minimum_requests} to judge health"
            ),
        )
        return UNKNOWN, [sample_rule, *rules]

    severities = {r.severity for r in rules}
    if "critical" in severities:
        return CRITICAL, rules
    if "degraded" in severities:
        return DEGRADED, rules
    return HEALTHY, rules


def reasons(status: str, rules: list[RuleResult]) -> list[str]:
    """Short human-readable reasons for the assigned status."""
    if status == UNKNOWN:
        return [rules[0].message]
    triggered = [r.message for r in rules if r.severity in ("critical", "degraded")]
    return triggered or ["All checks within thresholds"]
