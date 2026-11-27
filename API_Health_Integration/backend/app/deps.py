"""FastAPI dependencies: file store, selected file's logs, policy, time window."""
from __future__ import annotations

from fastapi import Depends, Query, Request

from app.config import HealthPolicy, Settings
from app.repositories.file_store import FileNotFound, FileStore
from app.repositories.log_repository import LogRepository
from app.schemas import WindowInfo
from app.services.time_window import resolve_window


def get_store(request: Request) -> FileStore:
    return request.app.state.store


def get_policy(request: Request) -> HealthPolicy:
    return request.app.state.policy


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_file_id(
    file_id: str | None = Query(None, description="Uploaded file to analyse (default: most recent)"),
    store: FileStore = Depends(get_store),
) -> str:
    if file_id:
        store.get(file_id)  # 404 if unknown
        return file_id
    latest = store.latest()
    if latest is None:
        raise FileNotFound("No log files uploaded yet")
    return latest.id


def get_repo(file_id: str = Depends(get_file_id), store: FileStore = Depends(get_store)) -> LogRepository:
    return store.repo(file_id)


def get_window(
    window: str = Query("1h", description="15m, 30m, 1h, 6h, 24h, 7d or all"),
    file_id: str = Depends(get_file_id),
    repo: LogRepository = Depends(get_repo),
    settings: Settings = Depends(get_settings),
) -> WindowInfo:
    return resolve_window(window, repo, settings.demo_mode, file_id)
