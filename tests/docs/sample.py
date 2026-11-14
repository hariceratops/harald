"""Builds the sample home the checked docs examples run against.

Run `python -m tests.docs.sample DIR` to build the same home by hand.
"""

import gzip
import json
import sys
from pathlib import Path

from click.testing import CliRunner

from harald.build.fetch import sidecar_path
from harald.build.publish import sha256_file
from harald.build.sources import DE_FILENAME, EN_FILENAME
from harald.cli import main
from harald.core.result import Result

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "docs" / "examples"

# also stated in docs/index.md
DOCS_SOURCE_DATE = "Sun, 01 Nov 2026 00:00:00 GMT"
CONFIG_TOML = "build_min_entries = 0\nbuild_workers = 0\n"


def docs_env(home: Path) -> dict[str, str | None]:
    return {
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(home / ".config"),
        "XDG_DATA_HOME": str(home / ".local" / "share"),
        "XDG_CACHE_HOME": str(home / ".cache"),
        "HARALD_CONFIG": None,
        "COLUMNS": "80",
        "FORCE_COLOR": None,
        "TTY_COMPATIBLE": None,
    }


def _write_source(sources: Path, filename: str, jsonl: Path) -> None:
    target = sources / filename
    # mtime=0 keeps the gzipped bytes, and so the sidecar's sha, stable
    with target.open("wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as gz:
        gz.write(jsonl.read_bytes())
    meta = {"sha256": sha256_file(target), "last_modified": DOCS_SOURCE_DATE}
    sidecar_path(sources, filename).write_text(json.dumps(meta), encoding="utf-8")


def build_sample_home(home: Path) -> Result[None, RuntimeError]:
    sources = home / ".local" / "share" / "harald" / "sources"
    sources.mkdir(parents=True)
    _write_source(sources, EN_FILENAME, EXAMPLES / "en-edition.jsonl")
    _write_source(sources, DE_FILENAME, EXAMPLES / "de-edition.jsonl")
    config = home / ".config" / "harald" / "config.toml"
    config.parent.mkdir(parents=True)
    config.write_text(CONFIG_TOML, encoding="utf-8")
    with CliRunner().isolation(env=docs_env(home)) as (_, _, output):
        code = main(["build"])
        text = output.getvalue().decode()
    if code != 0:
        return Result.err(RuntimeError(text))
    return Result.ok(None)


if __name__ == "__main__":
    built = build_sample_home(Path(sys.argv[1]))
    if built.is_err:
        sys.exit(str(built.unwrap_err()))
