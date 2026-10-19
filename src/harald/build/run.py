import os
import sqlite3
import time
from collections.abc import Iterable, Iterator
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from harald.build import reader
from harald.build.errors import (
    BuildError,
    BuildFailed,
    BuildLocked,
    SourceMissing,
    StagingNotSameFilesystem,
    TooFewEntries,
)
from harald.build.fetch import UNKNOWN_DATE, FetchOutcome, fetch_all, source_date
from harald.build.graph import JobOutput, Jobs
from harald.build.jobs import ParseCounts, fuzzy_range, parse_chunk
from harald.build.publish import (
    build_lock,
    fingerprint,
    is_unchanged,
    publish,
    record_build,
    sha256_file,
)
from harald.build.sources import EN_FILENAME, SOURCE_FILES
from harald.build.stage import SHARD_DDL
from harald.build.writer import (
    finalize,
    merge_fuzzy,
    merge_keys,
    merge_lexicon,
    open_staging,
)
from harald.config import Config
from harald.core.result import Result

CHUNK_BYTES = reader.CHUNK_BYTES


@dataclass(frozen=True)
class Timing:
    node: str
    seconds: float
    job_seconds: float | None = None


@dataclass(frozen=True)
class BuildReport:
    entries: int
    bad_lines: int
    size_bytes: int
    seconds: float
    unchanged: bool = False
    published: bool = True
    timings: tuple[Timing, ...] = ()
    fetched: tuple[FetchOutcome, ...] = ()
    # source files whose date could not be established, so the lexicon records "unknown"
    unknown_dates: tuple[str, ...] = ()


def build(
    config: Config, fetch: bool = False, force: bool = False
) -> Result[BuildReport, BuildError]:
    started = time.monotonic()
    source = config.sources_dir / EN_FILENAME
    if not fetch and not source.exists():
        return Result.err(SourceMissing(source))
    config.staging_dir.mkdir(parents=True, exist_ok=True)
    config.lexicon.parent.mkdir(parents=True, exist_ok=True)
    try:
        with build_lock(config.staging_dir):
            return _build_locked(config, source, fetch, force, started)
    except BuildLocked as e:
        return Result.err(e)


def _same_filesystem(a: Path, b: Path) -> bool:
    return a.stat().st_dev == b.stat().st_dev


def _build_locked(
    config: Config, source: Path, fetch: bool, force: bool, started: float
) -> Result[BuildReport, BuildError]:
    for leftover in config.staging_dir.glob("*.db"):
        leftover.unlink()
    if not _same_filesystem(config.staging_dir, config.lexicon.parent):
        return Result.err(StagingNotSameFilesystem(config.staging_dir, config.lexicon))
    staging = config.staging_dir / f"lexicon.{os.getpid()}.db"
    final = config.staging_dir / f"lexicon.final.{os.getpid()}.db"
    try:
        fetched: tuple[FetchOutcome, ...] = ()
        if fetch:
            fetch_res = fetch_all(config.sources_dir)
            if fetch_res.is_err:
                return Result.err(fetch_res.unwrap_err())
            fetched = fetch_res.unwrap().outcomes
        source_files = _source_files(config.sources_dir)
        unknown = tuple(f for f, _, date, _ in source_files if date == UNKNOWN_DATE)
        current = fingerprint(source_files)
        if not force and is_unchanged(config.staging_dir, config.lexicon, current):
            size = config.lexicon.stat().st_size
            return Result.ok(
                BuildReport(
                    0,
                    0,
                    size,
                    time.monotonic() - started,
                    unchanged=True,
                    published=False,
                    fetched=fetched,
                    unknown_dates=unknown,
                )
            )
        graph = _run_graph(config, source, source_files, staging, final)
        if graph.is_err:
            return Result.err(graph.unwrap_err())
        entries, bad_lines, timings = graph.unwrap()
        replaced = publish(final, config.lexicon)
        record_build(config.staging_dir, config.lexicon, current)
        size = config.lexicon.stat().st_size
    except Exception as e:  # noqa: BLE001 - failure seam: staging files must not survive
        return Result.err(BuildFailed("build", str(e)))
    finally:
        _remove_staging(config.staging_dir)
    return Result.ok(
        BuildReport(
            entries,
            bad_lines,
            size,
            time.monotonic() - started,
            published=replaced,
            timings=tuple(timings),
            fetched=fetched,
            unknown_dates=unknown,
        )
    )


def _run_graph(
    config: Config,
    source: Path,
    source_files: list[tuple[str, str, str, str]],
    staging: Path,
    final: Path,
) -> Result[tuple[int, int, list[Timing]], BuildError]:
    timings: list[Timing] = []
    con = open_staging(staging)
    jobs = Jobs(config.build_workers, config.staging_dir, SHARD_DDL)
    try:
        t = time.monotonic()
        with closing(reader.read_german_chunks(source, CHUNK_BYTES)) as chunks:
            parsed_out = jobs.run(
                "en.parse", parse_chunk, ((seq, (seq, chunk)) for seq, chunk in chunks)
            )
        if parsed_out.is_err:
            return Result.err(parsed_out.unwrap_err())
        outputs = parsed_out.unwrap()
        parsed: dict[int, ParseCounts] = {seq: o.value for seq, o in outputs.items()}
        timings.append(Timing("en.read+parse", time.monotonic() - t, _cpu(outputs.values())))
        entries = sum(p.entries for p in parsed.values())
        if entries < config.build_min_entries:
            return Result.err(TooFewEntries(entries, config.build_min_entries))
        parse_shards = sorted({o.shard for o in outputs.values()})

        t = time.monotonic()
        merge_lexicon(con, parse_shards, parsed)
        timings.append(Timing("lexicon.merge", time.monotonic() - t))
        t = time.monotonic()
        merge_keys(con, parse_shards)
        timings.append(Timing("keys.merge", time.monotonic() - t))

        t = time.monotonic()
        keys = con.execute("SELECT id, key FROM search_key ORDER BY id").fetchall()
        fuzzy_out = jobs.run("fuzzy", fuzzy_range, _slices(keys, max(config.build_workers, 1)))
        if fuzzy_out.is_err:
            return Result.err(fuzzy_out.unwrap_err())
        fuzzy_outputs = fuzzy_out.unwrap()
        timings.append(Timing("fuzzy", time.monotonic() - t, _cpu(fuzzy_outputs.values())))
        t = time.monotonic()
        merge_fuzzy(con, sorted({o.shard for o in fuzzy_outputs.values()}))
        timings.append(Timing("fuzzy.merge", time.monotonic() - t))

        t = time.monotonic()
        finalize(con, parsed, source_files)
        con.close()
        _vacuum_into(staging, final)
        timings.append(Timing("finalize", time.monotonic() - t))
    finally:
        # workers must be gone before their shard files are deleted
        jobs.close()
        con.close()
    return Result.ok((entries, sum(p.bad_lines for p in parsed.values()), timings))


def _source_files(sources_dir: Path) -> list[tuple[str, str, str, str]]:
    rows = []
    for f in SOURCE_FILES:
        path = sources_dir / f.filename
        if path.exists():
            sha = sha256_file(path)
            rows.append((f.filename, f.source, source_date(sources_dir, f.filename, sha), sha))
    return sorted(rows)


def _cpu(outputs: Iterable[JobOutput]) -> float:
    return sum(o.seconds for o in outputs)


def _slices(
    keys: list[tuple[int, str]], count: int
) -> Iterator[tuple[int, tuple[list[tuple[int, str]]]]]:
    """Contiguous key-id ranges; the split only decides who computes what, not the output."""
    size = max(1, -(-len(keys) // count))
    for n, i in enumerate(range(0, len(keys), size)):
        yield n, (keys[i : i + size],)


def _vacuum_into(src: Path, dst: Path) -> None:
    # VACUUM INTO canonicalises the file, so identical content gives identical bytes
    con = sqlite3.connect(src)
    try:
        con.execute("VACUUM INTO ?", (str(dst),))
    finally:
        con.close()


def _remove_staging(staging_dir: Path) -> None:
    # staging and shard files all end in .db; the staging directory belongs to Harald
    for p in staging_dir.glob("*.db"):
        p.unlink(missing_ok=True)
