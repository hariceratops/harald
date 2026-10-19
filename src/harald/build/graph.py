import multiprocessing
import sqlite3
import time
from collections.abc import Callable, Iterable
from concurrent.futures import FIRST_COMPLETED, Future, ProcessPoolExecutor, wait
from concurrent.futures.process import BrokenProcessPool
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from harald.build.errors import BuildError, BuildFailed, SourceUnreadable, TaskFailed
from harald.core.result import Result

# the connection this process writes its job rows to: a pool worker's own, or the main
# process's when build_workers is 0
_shard: sqlite3.Connection | None = None
_shard_path = ""


@dataclass(frozen=True)
class JobOutput:
    shard: str
    seconds: float
    value: Any


def init_worker(staging_dir: str, ddl: str) -> None:
    global _shard, _shard_path
    _shard_path = str(Path(staging_dir) / f"shard-{multiprocessing.current_process().pid}.db")
    _shard = sqlite3.connect(_shard_path, isolation_level=None)
    _shard.execute("PRAGMA journal_mode=OFF")
    _shard.execute("PRAGMA synchronous=OFF")
    _shard.executescript(ddl)


def _close_shard() -> None:
    global _shard
    if _shard is not None:
        _shard.close()
        _shard = None


def run_job(task: str, job: Callable[..., Any], *args: Any) -> Result[JobOutput, TaskFailed]:
    assert _shard is not None
    started = time.monotonic()
    try:
        _shard.execute("BEGIN")
        value = job(_shard, *args)
        _shard.execute("COMMIT")
    except Exception as e:  # noqa: BLE001 - failure seam: any job error becomes an Err
        return Result.err(TaskFailed(task, f"{type(e).__name__}: {e}"))
    return Result.ok(JobOutput(_shard_path, time.monotonic() - started, value))


class Jobs:
    """Runs jobs in a forkserver pool, or inline in this process when workers is 0.

    forkserver, because the reader threads are already running when the pool starts and
    forking a threaded process can deadlock.
    """

    def __init__(self, workers: int, staging_dir: Path, ddl: str) -> None:
        self.workers = workers
        self._pool: ProcessPoolExecutor | None = None
        if workers == 0:
            init_worker(str(staging_dir), ddl)
        else:
            self._pool = ProcessPoolExecutor(
                max_workers=workers,
                mp_context=multiprocessing.get_context("forkserver"),
                initializer=init_worker,
                initargs=(str(staging_dir), ddl),
            )

    def submit(
        self, task: str, job: Callable[..., Any], *args: Any
    ) -> Future[Result[JobOutput, TaskFailed]]:
        if self._pool is not None:
            return self._pool.submit(run_job, task, job, *args)
        done: Future[Result[JobOutput, TaskFailed]] = Future()
        done.set_result(run_job(task, job, *args))
        return done

    def run(
        self, task: str, job: Callable[..., Any], items: Iterable[tuple[int, tuple[Any, ...]]]
    ) -> Result[dict[int, JobOutput], BuildError]:
        """One job per (key, args), at most 2 x workers in flight; stops at the first Err."""
        limit = 2 * max(self.workers, 1)
        outputs: dict[int, JobOutput] = {}
        pending: dict[Future[Result[JobOutput, TaskFailed]], int] = {}
        try:
            for key, args in items:
                while len(pending) >= limit:
                    if (err := self._reap(task, pending, outputs)) is not None:
                        return Result.err(err)
                pending[self.submit(task, job, *args)] = key
            while pending:
                if (err := self._reap(task, pending, outputs)) is not None:
                    return Result.err(err)
        except SourceUnreadable as e:
            return Result.err(e)
        except BrokenProcessPool:
            return Result.err(BuildFailed(task, "a worker process died"))
        return Result.ok(outputs)

    @staticmethod
    def _reap(
        task: str,
        pending: dict[Future[Result[JobOutput, TaskFailed]], int],
        outputs: dict[int, JobOutput],
    ) -> BuildError | None:
        done, _ = wait(pending, return_when=FIRST_COMPLETED)
        for future in done:
            key = pending.pop(future)
            result = future.result()
            if result.is_err:
                return BuildFailed(task, str(result.unwrap_err()))
            outputs[key] = result.unwrap()
        return None

    def close(self) -> None:
        if self._pool is not None:
            self._pool.shutdown(wait=True, cancel_futures=True)
        else:
            _close_shard()
