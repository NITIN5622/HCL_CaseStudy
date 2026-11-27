import pytest

from app.repositories.log_repository import InMemoryLogRepository
from app.services.ingestion_service import InvalidEnvelopeError, ingest

GOOD = {"integration": "A", "timestamp": "2026-08-04T09:00:00", "status": "success",
        "status_code": 200, "latency_ms": 100}


def test_timeout_with_null_status_code_is_accepted():
    row = {**GOOD, "status": "timeout", "status_code": None, "latency_ms": 30000}
    summary, records = ingest({"logs": [row]}, set(), "test")
    assert summary.imported == 1 and records[0].status_code is None


@pytest.mark.parametrize(
    "bad",
    [
        {k: v for k, v in GOOD.items() if k != "status"},          # missing field
        {**GOOD, "latency_ms": -5},                                # negative latency
        {**GOOD, "timestamp": "not-a-date"},                       # malformed timestamp
        {**GOOD, "status": "exploded"},                            # unknown status
        "just a string",                                           # not an object
    ],
)
def test_invalid_rows_are_reported_not_imported(bad):
    summary, records = ingest({"logs": [GOOD, bad]}, set(), "test")
    assert (summary.received, summary.imported, summary.invalid) == (2, 1, 1)
    assert summary.errors[0].index == 1


@pytest.mark.parametrize("payload", [[], {"rows": []}, {"logs": "x"}, None])
def test_malformed_envelope_rejected(payload):
    with pytest.raises(InvalidEnvelopeError):
        ingest(payload, set(), "test")


def test_timestamps_normalized_to_utc():
    summary, records = ingest({"logs": [{**GOOD, "timestamp": "2026-08-04T14:30:00+05:30"}]}, set(), "test")
    assert records[0].timestamp.isoformat() == "2026-08-04T09:00:00+00:00"


def test_status_case_is_normalized():
    _, records = ingest({"logs": [{**GOOD, "status": " SUCCESS "}]}, set(), "test")
    assert records[0].status == "success"


def test_reimport_is_idempotent_and_out_of_order_is_sorted():
    repo = InMemoryLogRepository()
    later = {**GOOD, "timestamp": "2026-08-04T09:05:00"}
    first = repo.add_payload({"logs": [later, GOOD, GOOD]}, "seed")   # in-batch duplicate too
    assert (first.imported, first.duplicates) == (2, 1)
    again = repo.add_payload({"logs": [GOOD, later]}, "upload")
    assert (again.imported, again.duplicates) == (0, 2)
    times = [r.timestamp for r in repo.get_logs()]
    assert times == sorted(times)
