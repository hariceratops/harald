from pathlib import Path
from typing import Any

from sqlalchemy import Engine, event, inspect, text
from sqlalchemy.exc import OperationalError

from harald.core.result import Result
from harald.db.connection import make_engine
from harald.learning.errors import (
    LearningDbError,
    LearningDbTooNew,
    MigrationFailed,
    NotALearningDb,
)

HEAD = "0001"

SCRIPT_LOCATION = Path(__file__).parent / "migrations"


def stored_revision(engine: Engine) -> str | None:
    with engine.connect() as conn:
        try:
            return conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
        except OperationalError:
            return None


def migration_engine(path: Path) -> Engine:
    # SQLAlchemy's documented recipe for transactional DDL on pysqlite. It lives on this engine
    # only, so the runtime engine's transaction handling stays kohle's default.
    engine = make_engine(path)

    @event.listens_for(engine, "connect")
    def _no_implicit_begin(dbapi_connection: Any, _record: Any) -> None:
        dbapi_connection.isolation_level = None

    @event.listens_for(engine, "begin")
    def _begin(conn: Any) -> None:
        conn.exec_driver_sql("BEGIN")

    return engine


def _backup(engine: Engine, path: Path) -> Result[Path, LearningDbError]:
    target = path.with_name(f"{path.name}.pre-{HEAD}.bak")
    try:
        # a leftover from an earlier failed attempt; VACUUM INTO refuses to overwrite
        target.unlink(missing_ok=True)
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.exec_driver_sql("VACUUM INTO ?", (str(target),))
    except (OSError, OperationalError) as e:
        return Result.err(MigrationFailed("backup", str(e)))
    return Result.ok(target)


def upgrade(engine: Engine, path: Path, found: str | None) -> Result[None, LearningDbError]:
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    from alembic.util import CommandError

    config = Config()
    config.set_main_option("script_location", str(SCRIPT_LOCATION))
    scripts = ScriptDirectory.from_config(config)
    if found is not None:
        try:
            scripts.get_revision(found)
        except CommandError:
            return Result.err(LearningDbTooNew(found, HEAD))
    elif inspect(engine).get_table_names():
        return Result.err(NotALearningDb(path))

    if found is not None:
        backed_up = _backup(engine, path)
        if backed_up.is_err:
            return Result.err(backed_up.unwrap_err())

    return _run_upgrade(config, path)


def _run_upgrade(config: Any, path: Path) -> Result[None, LearningDbError]:
    from alembic import command

    migrating = migration_engine(path)
    try:
        with migrating.connect() as conn:
            config.attributes["connection"] = conn
            command.upgrade(config, "head")
    except Exception as e:  # noqa: BLE001
        return Result.err(MigrationFailed("upgrade", str(e)))
    finally:
        migrating.dispose()
    return Result.ok(None)
