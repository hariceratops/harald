from collections.abc import Mapping
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker


def make_engine(
    path: Path, *, pragmas: Mapping[str, str] | None = None, read_only: bool = False
) -> Engine:
    if read_only:
        # immutable: no locks, no -wal/-shm; safe because the file is replaced by rename
        return create_engine(f"sqlite+pysqlite:///file:{path}?mode=ro&immutable=1&uri=true")
    engine = create_engine(f"sqlite+pysqlite:///{path}")
    if pragmas:

        @event.listens_for(engine, "connect")
        def _set_pragmas(dbapi_connection: Any, _record: Any) -> None:
            cursor = dbapi_connection.cursor()
            for name, value in pragmas.items():
                cursor.execute(f"PRAGMA {name}={value}")
            cursor.close()

    return engine


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
