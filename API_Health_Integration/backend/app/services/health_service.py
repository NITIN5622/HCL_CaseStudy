"""Orchestrates repository -> metrics -> health engine -> failure analyzer.

Routers call this module; it holds no storage code and no HTTP code.
"""
from __future__ import annotations

from app.config import HealthPolicy
from app.domain import (
    CRITICAL, DEGRADED, HEALTHY, STATUS_SEVERITY, TIER_PRIORITY, UNKNOWN,
    LogRecord, integration_id,
)
from app.repositories.log_repository import LogRepository
from app.schemas import (
    Dashboard, DashboardSummary, IntegrationDetail, IntegrationSummary, WindowInfo,
)
from app.services import failure_analyzer, health_engine
from app.services.metrics_service import compute_metrics


class IntegrationNotFoundError(LookupError):
    pass


def _logs_in_window(repo: LogRepository, win: WindowInfo, name: str | None = None) -> list[LogRecord]:
    if win.end is None:  # empty store, historical mode
        return []
    return repo.get_logs(start=win.start, end=win.end, integration_name=name)


def build_detail(name: str, logs: list[LogRecord], policy: HealthPolicy, win: WindowInfo) -> IntegrationDetail:
    settings = policy.settings_for(name)
    metrics = compute_metrics(logs)
    status, rules = health_engine.evaluate(metrics, policy, settings)
    return IntegrationDetail(
        id=integration_id(name),
        name=name,
        tier=settings.tier,
        latency_slo_ms=settings.latency_slo_ms,
        health=status,
        metrics=metrics,
        rules=rules,
        reasons=health_engine.reasons(status, rules),
        dominant_failure=failure_analyzer.dominant_failure(metrics),
        recommendations=failure_analyzer.analyze(metrics, rules),
        window=win,
    )


def to_summary(d: IntegrationDetail) -> IntegrationSummary:
    return IntegrationSummary(
        id=d.id,
        name=d.name,
        tier=d.tier,
        health=d.health,
        total_requests=d.metrics.total_requests,
        successes=d.metrics.successes,
        errors=d.metrics.errors,
        timeouts=d.metrics.timeouts,
        failure_rate=d.metrics.failure_rate,
        timeout_rate=d.metrics.timeout_rate,
        avg_latency_ms=d.metrics.avg_latency_ms,
        dominant_failure=d.dominant_failure,
        reasons=d.reasons,
        next_step=d.recommendations[0].next_step if d.recommendations else None,
    )


def _attention_sort_key(s: IntegrationSummary):
    # Worst status first, then most important tier, then highest failure rate.
    return (-STATUS_SEVERITY[s.health], TIER_PRIORITY.get(s.tier, 9), -(s.failure_rate or 0), s.name)


def all_details(repo: LogRepository, policy: HealthPolicy, win: WindowInfo) -> list[IntegrationDetail]:
    # Every known integration is reported, even with no logs in the window
    # (it then shows as UNKNOWN rather than silently disappearing).
    logs = _logs_in_window(repo, win)
    by_name: dict[str, list[LogRecord]] = {name: [] for name in repo.integration_names()}
    for r in logs:
        by_name.setdefault(r.integration, []).append(r)
    return [build_detail(name, by_name[name], policy, win) for name in sorted(by_name)]


def get_detail(integration: str, repo: LogRepository, policy: HealthPolicy, win: WindowInfo) -> IntegrationDetail:
    name = resolve_name(integration, repo)
    return build_detail(name, _logs_in_window(repo, win, name), policy, win)


def resolve_name(integration: str, repo: LogRepository) -> str:
    for name in repo.integration_names():
        if integration_id(name) == integration:
            return name
    raise IntegrationNotFoundError(f"Unknown integration id: {integration}")


def build_dashboard(repo: LogRepository, policy: HealthPolicy, win: WindowInfo) -> Dashboard:
    details = all_details(repo, policy, win)
    summaries = sorted((to_summary(d) for d in details), key=_attention_sort_key)

    counts = {s: sum(1 for d in details if d.health == s) for s in (HEALTHY, DEGRADED, CRITICAL, UNKNOWN)}
    total_requests = sum(d.metrics.total_requests for d in details)
    total_failures = sum(d.metrics.errors + d.metrics.timeouts for d in details)
    overall = max((d.health for d in details), key=lambda s: STATUS_SEVERITY[s], default=UNKNOWN)

    return Dashboard(
        window=win,
        summary=DashboardSummary(
            total_integrations=len(details),
            healthy=counts[HEALTHY],
            degraded=counts[DEGRADED],
            critical=counts[CRITICAL],
            unknown=counts[UNKNOWN],
            overall_status=overall,
            total_requests=total_requests,
            total_failures=total_failures,
            # From summed counts, NOT the mean of per-integration rates.
            overall_failure_rate=(100.0 * total_failures / total_requests) if total_requests else None,
        ),
        needs_attention=[s for s in summaries if s.health != HEALTHY],
        integrations=summaries,
    )
