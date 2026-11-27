from fastapi import APIRouter, Depends

from app.config import HealthPolicy
from app.deps import get_policy, get_repo, get_window
from app.repositories.log_repository import LogRepository
from app.schemas import Dashboard, WindowInfo
from app.services.health_service import build_dashboard

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard", response_model=Dashboard)
def dashboard(
    win: WindowInfo = Depends(get_window),
    repo: LogRepository = Depends(get_repo),
    policy: HealthPolicy = Depends(get_policy),
):
    """KPI summary, Needs Attention list and per-integration health table."""
    return build_dashboard(repo, policy, win)
