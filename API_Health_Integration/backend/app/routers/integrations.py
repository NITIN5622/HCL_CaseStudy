from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.config import HealthPolicy
from app.deps import get_policy, get_repo, get_window
from app.repositories.log_repository import LogRepository
from app.routers.logs import paginate
from app.schemas import IntegrationDetail, IntegrationSummary, LogPage, Trends, WindowInfo
from app.services.health_service import (
    _attention_sort_key, _logs_in_window, all_details, get_detail, resolve_name, to_summary,
)
from app.services.trends import build_trends

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


@router.get("", response_model=list[IntegrationSummary])
def list_integrations(
    win: WindowInfo = Depends(get_window),
    repo: LogRepository = Depends(get_repo),
    policy: HealthPolicy = Depends(get_policy),
):
    """Health result for every integration, worst first."""
    return sorted((to_summary(d) for d in all_details(repo, policy, win)), key=_attention_sort_key)


@router.get("/{integration_id}", response_model=IntegrationDetail)
def integration_detail(
    integration_id: str,
    win: WindowInfo = Depends(get_window),
    repo: LogRepository = Depends(get_repo),
    policy: HealthPolicy = Depends(get_policy),
):
    """Metrics, every evaluated rule, reasons and recommendations for one integration."""
    return get_detail(integration_id, repo, policy, win)


@router.get("/{integration_id}/logs", response_model=LogPage)
def integration_logs(
    integration_id: str,
    win: WindowInfo = Depends(get_window),
    repo: LogRepository = Depends(get_repo),
    status: Literal["success", "error", "timeout", "failures"] | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
):
    """Raw logs for one integration in the window, newest first."""
    name = resolve_name(integration_id, repo)
    return paginate(_logs_in_window(repo, win, name), status, page, page_size)


@router.get("/{integration_id}/trends", response_model=Trends)
def integration_trends(
    integration_id: str,
    win: WindowInfo = Depends(get_window),
    repo: LogRepository = Depends(get_repo),
):
    """Requests per time bucket (success / error / timeout) and avg success latency."""
    name = resolve_name(integration_id, repo)
    return build_trends(_logs_in_window(repo, win, name), win)
