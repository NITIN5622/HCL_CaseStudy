"""Log pagination helper used by the integration logs endpoint."""
from app.domain import SUCCESS, LogRecord
from app.schemas import LogOut, LogPage


def paginate(logs: list[LogRecord], status: str | None, page: int, page_size: int) -> LogPage:
    if status == "failures":
        logs = [r for r in logs if r.status != SUCCESS]
    elif status:
        logs = [r for r in logs if r.status == status]
    logs = sorted(logs, key=lambda r: r.timestamp, reverse=True)
    start = (page - 1) * page_size
    items = [
        LogOut(
            integration_id=r.integration_id, integration=r.integration, timestamp=r.timestamp,
            status=r.status, status_code=r.status_code, latency_ms=r.latency_ms, source=r.source,
        )
        for r in logs[start:start + page_size]
    ]
    return LogPage(items=items, page=page, page_size=page_size, total=len(logs))
