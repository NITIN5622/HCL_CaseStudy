import pytest
from fastapi.testclient import TestClient

from app.config import BACKEND_DIR, Settings, load_policy
from app.main import create_app

STARTER = BACKEND_DIR / "tests" / "fixtures" / "integration_logs.json"


def make_settings(uploads_dir, **overrides) -> Settings:
    base = dict(
        uploads_dir=uploads_dir,
        config_file=BACKEND_DIR / "health_config.yaml",
        frontend_url="http://localhost:5173",
        admin_token=None,
        demo_mode=True,
        max_upload_bytes=1_000_000,
    )
    base.update(overrides)
    return Settings(**base)


def upload(client, body: bytes, name="logs.json", headers=None):
    return client.post("/api/files", files={"file": (name, body, "application/json")}, headers=headers or {})


@pytest.fixture
def policy():
    return load_policy(BACKEND_DIR / "health_config.yaml")


@pytest.fixture
def empty_client(tmp_path):
    """No files uploaded yet (first visit)."""
    return TestClient(create_app(make_settings(tmp_path / "uploads")))


@pytest.fixture
def client(empty_client):
    """Starter file uploaded; it is the most recent file."""
    r = upload(empty_client, STARTER.read_bytes(), "integration_logs.json")
    assert r.status_code == 201, r.text
    return empty_client
