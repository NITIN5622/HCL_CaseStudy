from dataclasses import asdict

from fastapi import APIRouter, Depends

from app.config import HealthPolicy, Settings
from app.deps import get_policy, get_settings, get_store
from app.repositories.file_store import FileStore

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health")
def backend_health(store: FileStore = Depends(get_store), settings: Settings = Depends(get_settings)):
    """Liveness check for the backend itself (not integration health)."""
    return {
        "status": "ok",
        "mode": "historical" if settings.demo_mode else "live",
        "files": len(store.list_files()),
    }


@router.get("/config/thresholds")
def thresholds(policy: HealthPolicy = Depends(get_policy)):
    """The health policy currently in force (from health_config.yaml)."""
    return asdict(policy)
