"""Recommendation engine: failure signal -> possible cause + next step.

These are POSSIBLE causes to guide investigation, never confirmed root causes.
No automatic remediation in the MVP.
"""
from __future__ import annotations

_PLAYBOOK: dict[str, tuple[str, str]] = {
    "HTTP 401": ("Possible authentication failure",
                 "Verify token expiry and stored credentials"),
    "HTTP 403": ("Possible permission failure",
                 "Check API permissions / scopes for this integration"),
    "HTTP 429": ("Rate limiting - we are sending too many requests (our side)",
                 "Review request frequency, quota and retry/backoff policy"),
    "HTTP 500": ("Upstream server error at the provider",
                 "Check provider status/errors and the failing request context"),
    "HTTP 502": ("Bad gateway between us and the provider",
                 "Check provider status and network path"),
    "HTTP 503": ("Provider service unavailable",
                 "Check provider status page / maintenance windows"),
    "HTTP 504": ("Gateway timeout at the provider",
                 "Check provider latency and our timeout settings"),
    "timeout": ("No response - possible provider slowness or network issue",
                "Investigate connectivity, provider response times and timeout settings"),
    "high_latency": ("Possible performance degradation",
                     "Review provider response times against the latency SLO"),
    "no_data": ("No recent requests - inactivity or an ingestion/logging issue",
                "Confirm the expected schedule and that the log pipeline is running"),
}

_GENERIC_4XX = ("Client-side request error (likely our configuration or payload)",
                "Inspect request payload and integration configuration")
_GENERIC_5XX = ("Upstream provider error", "Check provider status and error details")
_GENERIC = ("Unclassified failure", "Inspect raw logs for this integration")


def recommend(signal: str) -> tuple[str, str]:
    """Return (possible_cause, next_step) for a failure signal."""
    if signal in _PLAYBOOK:
        return _PLAYBOOK[signal]
    if signal.startswith("HTTP 4"):
        return _GENERIC_4XX
    if signal.startswith("HTTP 5"):
        return _GENERIC_5XX
    return _GENERIC
