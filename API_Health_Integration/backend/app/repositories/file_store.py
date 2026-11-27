"""Uploaded log files, persisted on disk.

    data/uploads/
      index.json        metadata for every uploaded file (newest last)
      <file_id>.json    the original uploaded content

Each file is analysed on its own. Parsed logs are cached in memory per file
(an InMemoryLogRepository), so the JSON is only parsed once per process.
Later, MongoDB can replace this class: same methods, different storage.
"""
from __future__ import annotations

import hashlib
import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.repositories.log_repository import InMemoryLogRepository
from app.schemas import FileInfo, ImportSummary
from app.services.ingestion_service import ingest


class FileNotFound(LookupError):
    pass


class DuplicateFileError(ValueError):
    def __init__(self, existing: FileInfo):
        super().__init__(f'This file is already uploaded as "{existing.filename}"')
        self.existing = existing


class NoValidLogsError(ValueError):
    def __init__(self, summary: ImportSummary):
        super().__init__("The file contains no valid log records")
        self.summary = summary


class FileStore:
    def __init__(self, uploads_dir: Path) -> None:
        self.dir = uploads_dir
        self.dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self.dir / "index.json"
        self._lock = threading.Lock()
        self._cache: dict[str, InMemoryLogRepository] = {}
        self._files: list[FileInfo] = self._read_index()

    # ------------------------------------------------------------ index ----
    def _read_index(self) -> list[FileInfo]:
        if not self._index_path.exists():
            return []
        with open(self._index_path, encoding="utf-8") as f:
            files = [FileInfo.model_validate(x) for x in json.load(f)]
        # Drop entries whose content file has gone missing.
        return [fi for fi in files if (self.dir / f"{fi.id}.json").exists()]

    def _write_index(self) -> None:
        tmp = self._index_path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump([fi.model_dump(mode="json") for fi in self._files], f, indent=2)
        tmp.replace(self._index_path)  # atomic swap: index is never half-written

    # ------------------------------------------------------------ reads ----
    def list_files(self) -> list[FileInfo]:
        """Newest first."""
        with self._lock:
            return sorted(self._files, key=lambda f: f.uploaded_at, reverse=True)

    def latest(self) -> FileInfo | None:
        files = self.list_files()
        return files[0] if files else None

    def get(self, file_id: str) -> FileInfo:
        with self._lock:
            for fi in self._files:
                if fi.id == file_id:
                    return fi
        raise FileNotFound(f"Unknown file id: {file_id}")

    def repo(self, file_id: str) -> InMemoryLogRepository:
        self.get(file_id)  # raises if unknown
        with self._lock:
            if file_id not in self._cache:
                repo = InMemoryLogRepository()
                with open(self.dir / f"{file_id}.json", encoding="utf-8") as f:
                    repo.add_payload(json.load(f), source=file_id)
                self._cache[file_id] = repo
            return self._cache[file_id]

    # ----------------------------------------------------------- writes ----
    def add(self, filename: str, body: bytes, payload: Any) -> tuple[FileInfo, ImportSummary]:
        content_hash = hashlib.sha256(body).hexdigest()
        with self._lock:
            for fi in self._files:
                if fi.content_hash == content_hash:
                    raise DuplicateFileError(fi)

        # Validate before saving anything (raises InvalidEnvelopeError on bad shape).
        summary, _ = ingest(payload, set(), source="upload")
        if summary.imported == 0:
            raise NoValidLogsError(summary)

        info = FileInfo(
            id=uuid.uuid4().hex[:12],
            filename=filename or "logs.json",
            uploaded_at=datetime.now(timezone.utc),
            log_count=summary.imported,
            invalid_count=summary.invalid,
            duplicate_count=summary.duplicates,
            content_hash=content_hash,
        )
        with self._lock:
            for fi in self._files:  # re-check: another upload may have won the race
                if fi.content_hash == content_hash:
                    raise DuplicateFileError(fi)
            (self.dir / f"{info.id}.json").write_bytes(body)
            self._files.append(info)
            self._write_index()
        return info, summary

    def delete(self, file_id: str) -> None:
        self.get(file_id)
        with self._lock:
            self._files = [fi for fi in self._files if fi.id != file_id]
            self._write_index()
            self._cache.pop(file_id, None)
            (self.dir / f"{file_id}.json").unlink(missing_ok=True)
