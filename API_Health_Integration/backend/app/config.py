"""Application settings (env vars) and the health policy (health_config.yaml)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

BACKEND_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class IntegrationSettings:
    tier: str
    latency_slo_ms: float


@dataclass(frozen=True)
class HealthPolicy:
    minimum_requests: int
    failure_degraded: float
    failure_critical: float
    timeout_degraded: float
    timeout_critical: float
    latency_critical_multiplier: float
    integrations: dict[str, IntegrationSettings] = field(default_factory=dict)
    default_integration: IntegrationSettings = IntegrationSettings("standard", 1000)

    def settings_for(self, integration_name: str) -> IntegrationSettings:
        return self.integrations.get(integration_name, self.default_integration)


@dataclass(frozen=True)
class Settings:
    uploads_dir: Path
    config_file: Path
    frontend_url: str
    admin_token: str | None
    demo_mode: bool
    max_upload_bytes: int


def load_settings() -> Settings:
    return Settings(
        # Uploaded log files are stored here (survive restarts).
        uploads_dir=Path(os.getenv("UPLOADS_DIR", BACKEND_DIR / "data" / "uploads")),
        config_file=Path(os.getenv("HEALTH_CONFIG", BACKEND_DIR / "health_config.yaml")),
        frontend_url=os.getenv("FRONTEND_URL", "http://localhost:5173"),
        # If ADMIN_TOKEN is set, uploads must send header X-Admin-Token.
        # If unset (local dev), uploads are allowed without a token.
        admin_token=os.getenv("ADMIN_TOKEN") or None,
        # Historical demo mode: "now" = latest log timestamp, not the wall clock.
        demo_mode=os.getenv("DEMO_MODE", "true").lower() == "true",
        max_upload_bytes=int(os.getenv("MAX_UPLOAD_BYTES", 1_000_000)),
    )


def load_policy(path: Path) -> HealthPolicy:
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    t = raw["health_thresholds"]
    integrations_raw = dict(raw.get("integrations", {}))
    default_raw = integrations_raw.pop("default", {"tier": "standard", "latency_slo_ms": 1000})

    def to_settings(d: dict) -> IntegrationSettings:
        return IntegrationSettings(tier=d["tier"], latency_slo_ms=float(d["latency_slo_ms"]))

    return HealthPolicy(
        minimum_requests=int(t["minimum_requests"]),
        failure_degraded=float(t["failure_rate"]["degraded"]),
        failure_critical=float(t["failure_rate"]["critical"]),
        timeout_degraded=float(t["timeout_rate"]["degraded"]),
        timeout_critical=float(t["timeout_rate"]["critical"]),
        latency_critical_multiplier=float(t["latency"]["critical_multiplier"]),
        integrations={name: to_settings(d) for name, d in integrations_raw.items()},
        default_integration=to_settings(default_raw),
    )
