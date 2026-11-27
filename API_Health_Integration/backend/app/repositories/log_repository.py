"""Repository layer: the ONLY place that knows where logs are stored.

Today: an in-memory store seeded from integration_logs.json.
Later: a MongoLogRepository implementing the same LogRepository protocol
can replace it without touching services, routers or the frontend.
"""
from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

from app.domain import LogRecord
from app.schemas import ImportSummary
from app.services.ingestion_service import ingest


class LogRepository(Protocol):
    def add_payload(self, payload: Any, source: str) -> ImportSummary: ...

    def get_logs(
        self,
        start: datetime | None = None,
        end: datetime | None = None,
        integration_name: str | None = None,
    ) -> list[LogRecord]: ...

    def integration_names(self) -> list[str]: ...

    def time_range(self) -> tuple[datetime | None, datetime | None]: ...

    def count(self) -> int: ...


class InMemoryLogRepository:
    """Thread-safe in-memory log store (data is lost on restart)."""

    def __init__(self) -> None:
        self._records: list[LogRecord] = []
        self._fingerprints: set[str] = set()
        self._lock = threading.Lock()

    # ------------------------------------------------------------ write ----
    def add_payload(self, payload: Any, source: str) -> ImportSummary:
        with self._lock:
            summary, records = ingest(payload, self._fingerprints, source)
            self._records.extend(records)
            self._fingerprints.update(r.fingerprint for r in records)
            self._records.sort(key=lambda r: r.timestamp)  # tolerate out-of-order input
            return summary

    def seed_from_file(self, path: Path) -> ImportSummary:
        with open(path, encoding="utf-8") as f:
            payload = json.load(f)
        return self.add_payload(payload, source="seed")

    # ------------------------------------------------------------- read ----
    def get_logs(
        self,
        start: datetime | None = None,
        end: datetime | None = None,
        integration_name: str | None = None,
    ) -> list[LogRecord]:
        """Logs with start < timestamp <= end (either bound optional), oldest first."""
        with self._lock:
            records = list(self._records)
        return [
            r
            for r in records
            if (start is None or r.timestamp > start)
            and (end is None or r.timestamp <= end)
            and (integration_name is None or r.integration == integration_name)
        ]

    def integration_names(self) -> list[str]:
        with self._lock:
            return sorted({r.integration for r in self._records})

    def time_range(self) -> tuple[datetime | None, datetime | None]:
        with self._lock:
            if not self._records:
                return None, None
            return self._records[0].timestamp, self._records[-1].timestamp

    def count(self) -> int:
        with self._lock:
            return len(self._records)
