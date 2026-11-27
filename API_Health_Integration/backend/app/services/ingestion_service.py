"""Log ingestion: validate -> normalize to UTC -> fingerprint -> dedupe.

Used by BOTH entry points (seed file at startup and JSON upload), so the
validation rules exist in exactly one place.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError

from app.domain import LogRecord
from app.schemas import ImportSummary, RawLog, RowError


class InvalidEnvelopeError(ValueError):
    """The payload is not of the form {"logs": [ ... ]}."""


def to_utc(ts: datetime) -> datetime:
    # Source timestamps have no offset; we ASSUME they are UTC (documented).
    if ts.tzinfo is None:
        return ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def fingerprint(raw: RawLog, ts_utc: datetime) -> str:
    # No request ID in the source, so identity = all fields. Trade-off: two
    # genuinely identical events would collapse into one (documented).
    canonical = "|".join(
        [raw.integration, ts_utc.isoformat(), raw.status, str(raw.status_code), f"{raw.latency_ms:g}"]
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _first_error(exc: ValidationError) -> str:
    err = exc.errors()[0]
    field = ".".join(str(p) for p in err["loc"]) or "record"
    return f"{field}: {err['msg']}"


def ingest(
    payload: Any,
    existing_fingerprints: set[str],
    source: str,
) -> tuple[ImportSummary, list[LogRecord]]:
    """Validate a {"logs": [...]} payload. Returns (summary, new records).

    Does not mutate existing_fingerprints; the caller stores the records.
    """
    if not isinstance(payload, dict) or not isinstance(payload.get("logs"), list):
        raise InvalidEnvelopeError('Expected a JSON object of the form {"logs": [ ... ]}')

    rows = payload["logs"]
    now = datetime.now(timezone.utc)
    seen = set(existing_fingerprints)
    records: list[LogRecord] = []
    errors: list[RowError] = []
    duplicates = 0

    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(RowError(index=index, error="record: must be a JSON object"))
            continue
        try:
            raw = RawLog.model_validate(row)
        except ValidationError as exc:
            errors.append(RowError(index=index, error=_first_error(exc)))
            continue

        ts = to_utc(raw.timestamp)
        fp = fingerprint(raw, ts)
        if fp in seen:
            duplicates += 1
            continue
        seen.add(fp)
        records.append(
            LogRecord(
                integration=raw.integration,
                timestamp=ts,
                status=raw.status,
                status_code=raw.status_code,
                latency_ms=raw.latency_ms,
                fingerprint=fp,
                source=source,
                ingested_at=now,
            )
        )

    summary = ImportSummary(
        received=len(rows),
        imported=len(records),
        invalid=len(errors),
        duplicates=duplicates,
        errors=errors,
    )
    return summary, records
