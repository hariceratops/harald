from dataclasses import dataclass
from pathlib import Path

from harald.build.errors import BuildError, BuildLocked, PruneFailed
from harald.build.fetch import part_path, sidecar_part_path, sidecar_path
from harald.build.publish import build_lock
from harald.build.sources import SOURCE_FILES
from harald.config import Config
from harald.core.result import Result


@dataclass(frozen=True)
class Prunable:
    path: Path
    size: int


def prunable(sources_dir: Path) -> list[Prunable]:
    # only names the fetch writes: anything else in the folder is the user's
    candidates = [
        path
        for f in SOURCE_FILES
        for path in (
            sources_dir / f.filename,
            sidecar_path(sources_dir, f.filename),
            part_path(sources_dir, f.filename),
            sidecar_part_path(sources_dir, f.filename),
        )
    ]
    return [Prunable(path, path.stat().st_size) for path in candidates if path.is_file()]


def prune_sources(config: Config) -> Result[int, BuildError]:
    config.staging_dir.mkdir(parents=True, exist_ok=True)
    try:
        # a running build is reading these files
        with build_lock(config.staging_dir):
            return _delete(prunable(config.sources_dir))
    except BuildLocked as e:
        return Result.err(e)


def _delete(files: list[Prunable]) -> Result[int, BuildError]:
    for deleted, f in enumerate(files):
        try:
            f.path.unlink()
        except OSError as e:
            return Result.err(PruneFailed(f.path, e.strerror or str(e), deleted))
    return Result.ok(sum(f.size for f in files))
