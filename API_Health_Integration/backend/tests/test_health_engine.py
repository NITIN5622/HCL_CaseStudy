import pytest

from app.config import IntegrationSettings
from app.schemas import IntegrationMetrics
from app.services.health_engine import evaluate

SETTINGS = IntegrationSettings(tier="standard", latency_slo_ms=500)


def metrics(total=12, failure=0.0, timeout=0.0, latency=100.0):
    return IntegrationMetrics(
        total_requests=total, successes=total, errors=0, timeouts=0,
        success_rate=100 - failure, error_rate=failure - timeout, timeout_rate=timeout,
        failure_rate=failure, avg_latency_ms=latency, p95_latency_ms=latency,
        last_success=None, last_seen=None, failure_counts=[],
    )


@pytest.mark.parametrize(
    "failure,expected",
    [(9.99, "healthy"), (10.0, "degraded"), (39.99, "degraded"), (40.0, "critical")],
)
def test_failure_rate_boundaries(policy, failure, expected):
    assert evaluate(metrics(failure=failure), policy, SETTINGS)[0] == expected


@pytest.mark.parametrize(
    "timeout,expected",
    [(4.99, "healthy"), (5.0, "degraded"), (20.0, "critical")],
)
def test_timeout_rate_boundaries(policy, timeout, expected):
    # failure rate kept below 10 so only the timeout rule can fire
    assert evaluate(metrics(failure=min(timeout, 9.0), timeout=timeout), policy, SETTINGS)[0] == expected


@pytest.mark.parametrize(
    "latency,expected",
    [(499, "healthy"), (500, "degraded"), (999, "degraded"), (1000, "critical")],
)
def test_latency_uses_per_integration_slo(policy, latency, expected):
    assert evaluate(metrics(latency=latency), policy, SETTINGS)[0] == expected


def test_critical_wins_and_all_rules_reported(policy):
    status, rules = evaluate(metrics(failure=15.0, timeout=25.0, latency=600), policy, SETTINGS)
    assert status == "critical"
    severities = {r.rule: r.severity for r in rules}
    assert severities == {"failure_rate": "degraded", "timeout_rate": "critical", "avg_latency_ms": "degraded"}


def test_too_few_requests_is_unknown(policy):
    status, rules = evaluate(metrics(total=4, failure=100.0), policy, SETTINGS)
    assert status == "unknown"
    assert rules[0].rule == "minimum_requests"


def test_null_latency_is_skipped_not_failed(policy):
    status, rules = evaluate(metrics(latency=None), policy, SETTINGS)
    assert status == "healthy"
    assert next(r for r in rules if r.rule == "avg_latency_ms").severity == "skipped"
