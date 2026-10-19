import hashlib
import json
import os
import urllib.request
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.error import HTTPError

from harald.build.errors import FetchFailed
from harald.build.sources import SOURCE_FILES, SourceFile
from harald.core.result import Result

UNKNOWN_DATE = "unknown"
_BLOCK = 1 << 20
_TIMEOUT_SECONDS = 60
_NOT_MODIFIED = 304


@dataclass(frozen=True)
class FetchOutcome:
    filename: str
    downloaded: bool


@dataclass(frozen=True)
class FetchReport:
    outcomes: tuple[FetchOutcome, ...]


def sidecar_path(sources_dir: Path, filename: str) -> Path:
    return sources_dir / f"{filename}.meta.json"


def fetch_all(
    sources_dir: Path, files: Sequence[SourceFile] = SOURCE_FILES
) -> Result[FetchReport, FetchFailed]:
    """Stops at the first failure; files already replaced stay current."""
    sources_dir.mkdir(parents=True, exist_ok=True)
    outcomes = []
    for f in files:
        res = _fetch_file(sources_dir, f)
        if res.is_err:
            return Result.err(res.unwrap_err())
        outcomes.append(FetchOutcome(f.filename, res.unwrap()))
    return Result.ok(FetchReport(tuple(outcomes)))


def source_date(sources_dir: Path, filename: str, sha256: str) -> str:
    """The Last-Modified date, trusted only while the sidecar still describes this file's bytes.

    File mtimes are never used: they would make the build nondeterministic.
    """
    try:
        meta = json.loads(sidecar_path(sources_dir, filename).read_text(encoding="utf-8"))
        if meta["sha256"] != sha256 or not meta["last_modified"]:
            return UNKNOWN_DATE
        return parsedate_to_datetime(meta["last_modified"]).astimezone(UTC).date().isoformat()
    except (OSError, ValueError, KeyError, TypeError):
        return UNKNOWN_DATE


def _conditional_headers(sources_dir: Path, filename: str) -> dict[str, str]:
    data = sources_dir / filename
    try:
        meta = json.loads(sidecar_path(sources_dir, filename).read_text(encoding="utf-8"))
        if not data.exists() or data.stat().st_size != meta["size"]:
            return {}
        headers = {}
        if meta.get("etag"):
            headers["If-None-Match"] = meta["etag"]
        if meta.get("last_modified"):
            headers["If-Modified-Since"] = meta["last_modified"]
        return headers
    except (OSError, ValueError, KeyError, TypeError):
        return {}


def _fetch_file(sources_dir: Path, f: SourceFile) -> Result[bool, FetchFailed]:
    """Returns whether a new copy was downloaded."""
    data = sources_dir / f.filename
    sidecar = sidecar_path(sources_dir, f.filename)
    part = sources_dir / f"{f.filename}.part"
    sidecar_part = sources_dir / f"{f.filename}.meta.json.part"
    request = urllib.request.Request(f.url, headers=_conditional_headers(sources_dir, f.filename))
    try:
        try:
            response = urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS)
        except HTTPError as e:
            if e.code == _NOT_MODIFIED:
                return Result.ok(False)
            raise
        with response:
            digest = hashlib.sha256()
            size = 0
            with part.open("wb") as out:
                while block := response.read(_BLOCK):
                    out.write(block)
                    digest.update(block)
                    size += len(block)
            expected = response.headers.get("Content-Length")
            if expected is not None and int(expected) != size:
                raise OSError(f"received {size} of {expected} bytes")
            meta = {
                "url": f.url,
                "etag": response.headers.get("ETag"),
                "last_modified": response.headers.get("Last-Modified"),
                "sha256": digest.hexdigest(),
                "size": size,
            }
        sidecar_part.write_text(json.dumps(meta), encoding="utf-8")
        os.replace(part, data)
        os.replace(sidecar_part, sidecar)
    except Exception as e:  # noqa: BLE001 - failure seam: the .part files must not survive
        part.unlink(missing_ok=True)
        sidecar_part.unlink(missing_ok=True)
        return Result.err(FetchFailed(f.filename, str(e)))
    return Result.ok(True)
