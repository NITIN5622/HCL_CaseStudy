"""Pydantic models: incoming log validation and typed API responses."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

HealthStatus = Literal["healthy", "degraded", "critical", "unknown"]
RuleSeverity = Literal["ok", "degraded", "critical", "skipped"]


# ---------------------------------------------------------------- input ----
class RawLog(BaseModel):
    """One log row as it appears in integration_logs.json."""

    model_config = ConfigDict(extra="ignore")  # tolerate future extra fields

    integration: str = Field(min_length=1)
    timestamp: datetime
    status: Literal["success", "error", "timeout"]
    status_code: int | None = None
    latency_ms: float = Field(ge=0)

    @field_validator("integration", mode="before")
    @classmethod
    def strip_name(cls, v):
        return v.strip() if isinstance(v, str) else v

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, v):
        return v.strip().lower() if isinstance(v, str) else v


class RowError(BaseModel):
    index: int
    error: str


class ImportSummary(BaseModel):
    received: int
    imported: int
    invalid: int
    duplicates: int
    errors: list[RowError] = []


# --------------------------------------------------------------- files ----
class FileInfo(BaseModel):
    id: str
    filename: str
    uploaded_at: datetime
    log_count: int
    invalid_count: int
    duplicate_count: int
    content_hash: str


class FileUploadResult(BaseModel):
    file: FileInfo
    summary: ImportSummary


class FileDeleteResult(BaseModel):
    deleted: str
    remaining: int
    latest_file_id: str | None


# ------------------------------------------------------------- metrics ----
class FailureCount(BaseModel):
    failure: str  # "timeout", "HTTP 500", "HTTP 429", ...
    count: int


class IntegrationMetrics(BaseModel):
    total_requests: int
    successes: int
    errors: int
    timeouts: int
    success_rate: float | None
    error_rate: float | None
    timeout_rate: float | None
    failure_rate: float | None
    avg_latency_ms: float | None  # successful requests only
    p95_latency_ms: float | None  # successful requests only, nearest-rank
    last_success: datetime | None
    last_seen: datetime | None
    failure_counts: list[FailureCount]


# -------------------------------------------------------------- health ----
class RuleResult(BaseModel):
    rule: str
    value: float | None
    degraded_threshold: float
    critical_threshold: float
    severity: RuleSeverity
    message: str


class Recommendation(BaseModel):
    signal: str
    count: int
    possible_cause: str
    next_step: str


class IntegrationSummary(BaseModel):
    id: str
    name: str
    tier: str
    health: HealthStatus
    total_requests: int
    successes: int
    errors: int
    timeouts: int
    failure_rate: float | None
    timeout_rate: float | None
    avg_latency_ms: float | None
    dominant_failure: str | None
    reasons: list[str]
    next_step: str | None


class IntegrationDetail(BaseModel):
    id: str
    name: str
    tier: str
    latency_slo_ms: float
    health: HealthStatus
    metrics: IntegrationMetrics
    rules: list[RuleResult]
    reasons: list[str]
    dominant_failure: str | None
    recommendations: list[Recommendation]
    window: "WindowInfo"


# ----------------------------------------------------------- dashboard ----
class WindowInfo(BaseModel):
    file_id: str | None = None
    mode: Literal["historical", "live"]
    window: str
    start: datetime | None  # exclusive
    end: datetime | None  # inclusive (reference time)
    data_earliest: datetime | None
    data_latest: datetime | None


class DashboardSummary(BaseModel):
    total_integrations: int
    healthy: int
    degraded: int
    critical: int
    unknown: int
    overall_status: HealthStatus
    total_requests: int
    total_failures: int
    overall_failure_rate: float | None


class Dashboard(BaseModel):
    window: WindowInfo
    summary: DashboardSummary
    needs_attention: list[IntegrationSummary]
    integrations: list[IntegrationSummary]


# ---------------------------------------------------------------- logs ----
class LogOut(BaseModel):
    integration_id: str
    integration: str
    timestamp: datetime
    status: str
    status_code: int | None
    latency_ms: float
    source: str


class LogPage(BaseModel):
    items: list[LogOut]
    page: int
    page_size: int
    total: int


# -------------------------------------------------------------- trends ----
class TrendBucket(BaseModel):
    start: datetime
    success: int
    error: int
    timeout: int
    avg_latency_ms: float | None  # successful requests only


class Trends(BaseModel):
    bucket_minutes: int
    buckets: list[TrendBucket]


IntegrationDetail.model_rebuild()
