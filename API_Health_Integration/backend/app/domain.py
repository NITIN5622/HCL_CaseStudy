"""Core domain objects shared by every layer."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

SUCCESS = "success"
ERROR = "error"
TIMEOUT = "timeout"
VALID_STATUSES = (SUCCESS, ERROR, TIMEOUT)

HEALTHY = "healthy"
DEGRADED = "degraded"
CRITICAL = "critical"
UNKNOWN = "unknown"

# Used to sort "Needs Attention" and pick the worst overall status.
STATUS_SEVERITY = {CRITICAL: 3, DEGRADED: 2, UNKNOWN: 1, HEALTHY: 0}
TIER_PRIORITY = {"critical": 0, "standard": 1, "low": 2}


@dataclass(frozen=True)
class LogRecord:
    """One validated, normalized request-log entry (timestamp is UTC-aware)."""

    integration: str
    timestamp: datetime
    status: str
    status_code: int | None
    latency_ms: float
    fingerprint: str
    source: str
    ingested_at: datetime

    @property
    def integration_id(self) -> str:
        return integration_id(self.integration)

    @property
    def failure_key(self) -> str | None:
        """How this request failed, or None if it succeeded."""
        if self.status == SUCCESS:
            return None
        if self.status == TIMEOUT:
            return "timeout"
        return f"HTTP {self.status_code}" if self.status_code is not None else "error (no code)"


def integration_id(name: str) -> str:
    """Stable URL-safe id, e.g. 'Greenhouse ATS Sync' -> 'greenhouse-ats-sync'."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
