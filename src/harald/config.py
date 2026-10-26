import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

from harald.core.result import Result


class ConfigError(Exception):
    def __init__(self, path: Path, detail: str) -> None:
        super().__init__(f"{path}: {detail}")
        self.path = path
        self.detail = detail


@dataclass(frozen=True)
class Config:
    lexicon: Path
    sources_dir: Path
    staging_dir: Path
    build_min_entries: int
    build_workers: int = max(1, (os.cpu_count() or 2) - 1)
    learning_db: Path = Path("learning.db")


def _xdg(var: str, fallback: str) -> Path:
    return Path(os.environ.get(var) or Path.home() / fallback)


def default_config_path() -> Path:
    return _xdg("XDG_CONFIG_HOME", ".config") / "harald" / "config.toml"


def load_config(path: Path | None = None) -> Result[Config, ConfigError]:
    explicit = path is not None
    path = path or default_config_path()
    data_dir = _xdg("XDG_DATA_HOME", ".local/share") / "harald"
    values: dict[str, object] = {}
    if explicit or path.exists():
        try:
            values = tomllib.loads(path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError) as e:
            return Result.err(ConfigError(path, str(e)))

    paths = {
        "lexicon": data_dir / "lexicon.db",
        "learning_db": data_dir / "learning.db",
        "sources_dir": data_dir / "sources",
        "staging_dir": _xdg("XDG_CACHE_HOME", ".cache") / "harald" / "staging",
    }
    min_entries = 50_000
    workers = Config.build_workers
    for key, value in values.items():
        if key in paths and isinstance(value, str):
            paths[key] = Path(value).expanduser()
        elif key == "build_min_entries" and isinstance(value, int):
            min_entries = value
        elif key == "build_workers" and isinstance(value, int) and value >= 0:
            workers = value
        else:
            return Result.err(ConfigError(path, f"unknown or invalid key {key!r}"))
    return Result.ok(
        Config(
            paths["lexicon"],
            paths["sources_dir"],
            paths["staging_dir"],
            min_entries,
            workers,
            paths["learning_db"],
        )
    )
