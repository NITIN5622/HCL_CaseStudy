"""FastAPI entry point.  Run:  uvicorn app.main:app --reload"""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import Settings, load_policy, load_settings
from app.repositories.file_store import DuplicateFileError, FileNotFound, FileStore, NoValidLogsError
from app.routers import dashboard, files, integrations, system
from app.services.health_service import IntegrationNotFoundError
from app.services.ingestion_service import InvalidEnvelopeError
from app.services.time_window import InvalidWindowError

log = logging.getLogger("health_monitor")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()

    app = FastAPI(
        title="Brightline HR - Integration Health Monitor",
        description="Rule-based health checks over uploaded integration request-log files.",
        version="1.1.0",
    )

    # Shared state: uploaded files on disk (JSON for now) + health policy.
    app.state.store = FileStore(settings.uploads_dir)
    app.state.policy = load_policy(settings.config_file)
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url, "http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["*"],
    )

    # ------------------------------------------------- error handling ----
    @app.exception_handler(InvalidWindowError)
    @app.exception_handler(InvalidEnvelopeError)
    async def bad_request(_: Request, exc: Exception):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(IntegrationNotFoundError)
    @app.exception_handler(FileNotFound)
    async def not_found(_: Request, exc: Exception):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(DuplicateFileError)
    async def duplicate(_: Request, exc: DuplicateFileError):
        return JSONResponse(status_code=409, content={"detail": str(exc), "existing_file_id": exc.existing.id})

    @app.exception_handler(NoValidLogsError)
    async def no_valid_logs(_: Request, exc: NoValidLogsError):
        return JSONResponse(status_code=422, content={"detail": str(exc), "summary": exc.summary.model_dump()})

    @app.exception_handler(Exception)
    async def unexpected(_: Request, exc: Exception):
        log.exception("Unhandled error")  # full trace in server logs only
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    for r in (system.router, files.router, dashboard.router, integrations.router):
        app.include_router(r)

    return app


app = create_app()
