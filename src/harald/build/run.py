import json
import os
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

from harald.build.errors import (
    BuildError,
    BuildFailed,
    BuildLocked,
    SourceMissing,
    SourceUnreadable,
    StagingNotSameFilesystem,
    TooFewEntries,
)
from harald.build.publish import build_lock, fingerprint, is_unchanged, publish, record_build
from harald.build.reader import read_german_lines
from harald.build.records import EntryRecord, FormOfRecord
from harald.build.sources import EN_FILENAME
from harald.build.wiktextract_en import parse_line
from harald.build.writer import write_lexicon
from harald.config import Config
from harald.core.result import Result


@dataclass(frozen=True)
class BuildReport:
    entries: int
    bad_lines: int
    size_bytes: int
    seconds: float
    unchanged: bool = False
    published: bool = True


def build(config: Config, force: bool = False) -> Result[BuildReport, BuildError]:
    started = time.monotonic()
    source = config.sources_dir / EN_FILENAME
    if not source.exists():
        return Result.err(SourceMissing(source))
    config.staging_dir.mkdir(parents=True, exist_ok=True)
    config.lexicon.parent.mkdir(parents=True, exist_ok=True)
    try:
        with build_lock(config.staging_dir):
            return _build_locked(config, source, force, started)
    except BuildLocked as e:
        return Result.err(e)


def _same_filesystem(a: Path, b: Path) -> bool:
    return a.stat().st_dev == b.stat().st_dev


def _build_locked(
    config: Config, source: Path, force: bool, started: float
) -> Result[BuildReport, BuildError]:
    for leftover in config.staging_dir.glob("*.db"):
        leftover.unlink()
    if not _same_filesystem(config.staging_dir, config.lexicon.parent):
        return Result.err(StagingNotSameFilesystem(config.staging_dir, config.lexicon))
    staging = config.staging_dir / f"lexicon.{os.getpid()}.db"
    final = config.staging_dir / f"lexicon.final.{os.getpid()}.db"
    try:
        current = fingerprint([source])
        if not force and is_unchanged(config.staging_dir, config.lexicon, current):
            size = config.lexicon.stat().st_size
            return Result.ok(
                BuildReport(0, 0, size, time.monotonic() - started, unchanged=True, published=False)
            )
        records: list[EntryRecord] = []
        form_ofs: list[FormOfRecord] = []
        bad_lines = 0
        for line in read_german_lines(source):
            try:
                record = parse_line(line)
            except json.JSONDecodeError:
                bad_lines += 1
                continue
            if isinstance(record, EntryRecord):
                records.append(record)
            elif record is not None:
                form_ofs.append(record)
        if len(records) < config.build_min_entries:
            return Result.err(TooFewEntries(len(records), config.build_min_entries))
        write_lexicon(staging, records, form_ofs)
        _vacuum_into(staging, final)
        staging.unlink()
        replaced = publish(final, config.lexicon)
        record_build(config.staging_dir, config.lexicon, current)
        size = config.lexicon.stat().st_size
    except SourceUnreadable as e:
        return Result.err(e)
    except Exception as e:  # noqa: BLE001 - failure seam: staging files must not survive
        return Result.err(BuildFailed("build", str(e)))
    finally:
        _remove(staging, final)
    return Result.ok(
        BuildReport(len(records), bad_lines, size, time.monotonic() - started, published=replaced)
    )


def _vacuum_into(src: Path, dst: Path) -> None:
    # VACUUM INTO canonicalises the file, so identical content gives identical bytes
    con = sqlite3.connect(src)
    try:
        con.execute("VACUUM INTO ?", (str(dst),))
    finally:
        con.close()


def _remove(*paths: Path) -> None:
    for p in paths:
        p.unlink(missing_ok=True)
