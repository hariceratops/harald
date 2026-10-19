import fcntl
import filecmp
import hashlib
import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import harald
from harald.build.errors import BuildLocked
from harald.lexicon.schema import SCHEMA_VERSION

_LAST_BUILD = "last_build.json"


@contextmanager
def build_lock(staging_dir: Path) -> Iterator[None]:
    lock = staging_dir / ".lock"
    with lock.open("a") as f:
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as e:
            raise BuildLocked(lock) from e
        yield


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def fingerprint(sources: list[Path]) -> str:
    """Covers everything that can change the output: schema, importer code, source bytes."""
    digest = hashlib.sha256()
    digest.update(f"schema:{SCHEMA_VERSION}\n".encode())
    package = Path(harald.__file__).parent
    for py in sorted(package.rglob("*.py")):
        digest.update(py.relative_to(package).as_posix().encode() + b"\0")
        digest.update(py.read_bytes() + b"\0")
    for source in sorted(sources):
        digest.update(f"{source.name}:{sha256_file(source)}\n".encode())
    return digest.hexdigest()


def is_unchanged(staging_dir: Path, published: Path, current: str) -> bool:
    record = staging_dir / _LAST_BUILD
    if not published.exists() or not record.exists():
        return False
    try:
        last = json.loads(record.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return bool(last.get("fingerprint") == current and last.get("sha256") == sha256_file(published))


def publish(final: Path, published: Path) -> bool:
    """Returns False, leaving the published file untouched, when the bytes are identical."""
    if published.exists() and filecmp.cmp(final, published, shallow=False):
        final.unlink()
        return False
    _fsync(final)
    os.replace(final, published)
    _fsync(published.parent)
    return True


def record_build(staging_dir: Path, published: Path, current: str) -> None:
    record = staging_dir / _LAST_BUILD
    tmp = staging_dir / f"{_LAST_BUILD}.tmp"
    tmp.write_text(
        json.dumps({"fingerprint": current, "sha256": sha256_file(published)}), encoding="utf-8"
    )
    os.replace(tmp, record)


def _fsync(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
