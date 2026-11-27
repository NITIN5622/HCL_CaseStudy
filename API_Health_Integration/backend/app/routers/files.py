import json
import secrets

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile

from app.config import Settings
from app.deps import get_settings, get_store
from app.repositories.file_store import FileStore
from app.schemas import FileDeleteResult, FileInfo, FileUploadResult

router = APIRouter(prefix="/api/files", tags=["files"])


def require_admin(
    x_admin_token: str | None = Header(None),
    settings: Settings = Depends(get_settings),
) -> None:
    """If ADMIN_TOKEN is configured, uploads and deletes must send it."""
    if settings.admin_token and not (
        x_admin_token and secrets.compare_digest(x_admin_token, settings.admin_token)
    ):
        raise HTTPException(status_code=401, detail="This action requires a valid X-Admin-Token header")


@router.get("", response_model=list[FileInfo])
def list_files(store: FileStore = Depends(get_store)):
    """All uploaded log files, newest first."""
    return store.list_files()


@router.post("", response_model=FileUploadResult, status_code=201, dependencies=[Depends(require_admin)])
async def upload_file(
    file: UploadFile = File(..., description='JSON file of the form {"logs": [...]}'),
    store: FileStore = Depends(get_store),
    settings: Settings = Depends(get_settings),
):
    """Validate and store a log file. Rejects exact duplicates (409) and files with no valid logs (422)."""
    body = await file.read(settings.max_upload_bytes + 1)
    if len(body) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail=f"File larger than {settings.max_upload_bytes} bytes")
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise HTTPException(status_code=400, detail="File is not valid UTF-8 JSON")

    info, summary = store.add(file.filename or "logs.json", body, payload)
    return FileUploadResult(file=info, summary=summary)


@router.delete("/{file_id}", response_model=FileDeleteResult, dependencies=[Depends(require_admin)])
def delete_file(file_id: str, store: FileStore = Depends(get_store)):
    """Delete an uploaded file. Returns what is left so the UI can switch files."""
    store.delete(file_id)
    remaining = store.list_files()
    return FileDeleteResult(
        deleted=file_id,
        remaining=len(remaining),
        latest_file_id=remaining[0].id if remaining else None,
    )
