"""End-to-end checks against the provided starter data."""
import pytest

EXPECTED = {
    # id: (health, failure_rate, successes, errors, timeouts)
    "greenhouse-ats-sync": ("critical", 50.0, 6, 1, 5),
    "adp-payroll-sync": ("critical", 41.6667, 7, 5, 0),
    "docusign-envelope-api": ("degraded", 33.3333, 8, 4, 0),
    "slack-notifications": ("healthy", 8.3333, 11, 1, 0),
    "workday-directory-sync": ("healthy", 8.3333, 11, 1, 0),
}


def test_dashboard_summary_matches_expected(client):
    d = client.get("/api/dashboard?window=1h").json()
    s = d["summary"]
    assert d["window"]["mode"] == "historical"
    assert d["window"]["end"].startswith("2026-08-04T09:55:00")
    assert (s["total_integrations"], s["healthy"], s["degraded"], s["critical"], s["unknown"]) == (5, 2, 1, 2, 0)
    assert (s["total_requests"], s["total_failures"]) == (60, 17)
    assert s["overall_failure_rate"] == pytest.approx(28.3333, abs=1e-3)
    assert s["overall_status"] == "critical"


def test_needs_attention_order(client):
    d = client.get("/api/dashboard").json()
    # critical first; within critical, payroll (critical tier) before Greenhouse
    assert [i["id"] for i in d["needs_attention"]] == [
        "adp-payroll-sync", "greenhouse-ats-sync", "docusign-envelope-api",
    ]


@pytest.mark.parametrize("iid", EXPECTED)
def test_each_integration_classification(client, iid):
    health, rate, s, e, t = EXPECTED[iid]
    d = client.get(f"/api/integrations/{iid}").json()
    m = d["metrics"]
    assert d["health"] == health
    assert m["failure_rate"] == pytest.approx(rate, abs=1e-3)
    assert (m["successes"], m["errors"], m["timeouts"]) == (s, e, t)


def test_docusign_not_flagged_for_latency(client):
    d = client.get("/api/integrations/docusign-envelope-api").json()
    latency = next(r for r in d["rules"] if r["rule"] == "avg_latency_ms")
    assert latency["severity"] == "ok"
    assert d["dominant_failure"] == "HTTP 429"
    assert "rate limit" in d["recommendations"][0]["possible_cause"].lower()


def test_short_window_with_few_requests_is_unknown(client):
    # 15m window ending 09:55 -> only 09:45, 09:50, 09:55 (3 per integration)
    d = client.get("/api/dashboard?window=15m").json()
    assert d["summary"]["unknown"] == 5
    assert d["summary"]["total_requests"] == 15


def test_errors(client):
    assert client.get("/api/dashboard?window=banana").status_code == 400
    assert client.get("/api/integrations/does-not-exist").status_code == 404
    assert client.get("/api/integrations/adp-payroll-sync/logs?page=0").status_code == 422


def test_logs_pagination_and_failure_filter(client):
    r = client.get("/api/integrations/adp-payroll-sync/logs?status=failures&page_size=2").json()
    assert r["total"] == 5 and len(r["items"]) == 2
    assert r["items"][0]["timestamp"].startswith("2026-08-04T09:45")  # newest first


