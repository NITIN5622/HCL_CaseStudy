"""Upload page / file selector / delete behaviour."""
import json

from fastapi.testclient import TestClient

from app.main import create_app
from tests.conftest import STARTER, make_settings, upload


def small_file(minute: int) -> bytes:
    rows = [
        {"integration": "Slack Notifications", "timestamp": f"2026-09-01T10:{minute:02d}:00",
         "status": "success", "status_code": 200, "latency_ms": 100 + i}
        for i in range(6)
    ]
    return json.dumps({"logs": rows}).encode()


def test_first_visit_has_no_files_and_dashboard_404(empty_client):
    assert empty_client.get("/api/files").json() == []
    r = empty_client.get("/api/dashboard")
    assert r.status_code == 404 and "No log files" in r.json()["detail"]


def test_upload_returns_file_and_summary(empty_client):
    r = upload(empty_client, STARTER.read_bytes(), "integration_logs.json")
    assert r.status_code == 201
    body = r.json()
    assert body["file"]["filename"] == "integration_logs.json"
    assert body["file"]["log_count"] == 60
    assert body["summary"] == {"received": 60, "imported": 60, "invalid": 0, "duplicates": 0, "errors": []}
    assert [f["id"] for f in empty_client.get("/api/files").json()] == [body["file"]["id"]]


def test_same_file_twice_is_rejected(client):
    r = upload(client, STARTER.read_bytes(), "copy.json")
    assert r.status_code == 409
    assert "already uploaded" in r.json()["detail"]
    assert len(client.get("/api/files").json()) == 1


def test_bad_uploads(empty_client):
    assert upload(empty_client, b"{not json").status_code == 400
    assert upload(empty_client, b'{"rows": []}').status_code == 400
    r = upload(empty_client, json.dumps({"logs": [{"status": "nope"}]}).encode())
    assert r.status_code == 422 and r.json()["summary"]["invalid"] == 1
    assert empty_client.get("/api/files").json() == []  # nothing saved


def test_newest_file_is_default_and_file_id_selects(client):
    starter_id = client.get("/api/files").json()[0]["id"]
    new_id = upload(client, small_file(0), "new.json").json()["file"]["id"]

    files = client.get("/api/files").json()
    assert [f["id"] for f in files] == [new_id, starter_id]  # newest first

    default = client.get("/api/dashboard").json()
    assert default["window"]["file_id"] == new_id
    assert default["summary"]["total_integrations"] == 1

    chosen = client.get(f"/api/dashboard?file_id={starter_id}").json()
    assert chosen["summary"]["total_requests"] == 60

    assert client.get("/api/dashboard?file_id=nope").status_code == 404


def test_delete_switches_to_latest_then_empty(client):
    starter_id = client.get("/api/files").json()[0]["id"]
    new_id = upload(client, small_file(0), "new.json").json()["file"]["id"]

    r = client.delete(f"/api/files/{new_id}").json()
    assert r == {"deleted": new_id, "remaining": 1, "latest_file_id": starter_id}

    r = client.delete(f"/api/files/{starter_id}").json()
    assert r == {"deleted": starter_id, "remaining": 0, "latest_file_id": None}
    assert client.get("/api/dashboard").status_code == 404
    assert client.delete(f"/api/files/{starter_id}").status_code == 404


def test_files_survive_restart(tmp_path):
    settings = make_settings(tmp_path / "uploads")
    c1 = TestClient(create_app(settings))
    file_id = upload(c1, STARTER.read_bytes()).json()["file"]["id"]

    c2 = TestClient(create_app(settings))  # simulated restart
    assert [f["id"] for f in c2.get("/api/files").json()] == [file_id]
    assert c2.get("/api/dashboard").json()["summary"]["total_requests"] == 60


def test_upload_and_delete_require_token_when_configured(tmp_path):
    c = TestClient(create_app(make_settings(tmp_path / "u", admin_token="s3cret")))
    assert upload(c, STARTER.read_bytes()).status_code == 401
    r = upload(c, STARTER.read_bytes(), headers={"X-Admin-Token": "s3cret"})
    assert r.status_code == 201
    fid = r.json()["file"]["id"]
    assert c.delete(f"/api/files/{fid}").status_code == 401
    assert c.delete(f"/api/files/{fid}", headers={"X-Admin-Token": "s3cret"}).status_code == 200


def test_trends_buckets(client):
    t = client.get("/api/integrations/greenhouse-ats-sync/trends?window=1h").json()
    assert t["bucket_minutes"] == 5
    assert len(t["buckets"]) == 12
    assert sum(b["timeout"] for b in t["buckets"]) == 5
    assert sum(b["success"] for b in t["buckets"]) == 6
    assert t["buckets"][0]["start"].startswith("2026-08-04T09:00")
