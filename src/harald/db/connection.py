from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


def make_engine(path: Path, read_only: bool = False) -> Engine:
    if read_only:
        # immutable: no locks, no -wal/-shm; safe because the file is replaced by rename
        return create_engine(f"sqlite+pysqlite:///file:{path}?mode=ro&immutable=1&uri=true")
    return create_engine(f"sqlite+pysqlite:///{path}")


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)
