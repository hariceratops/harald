from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path

from sqlalchemy import Engine, select
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import Session, sessionmaker

from harald.core.result import Result
from harald.db.connection import make_engine, make_session_factory
from harald.lexicon.errors import LexiconError, LexiconMissing, NotALexicon, SchemaMismatch
from harald.lexicon.models import Meta
from harald.lexicon.schema import SCHEMA_VERSION


@dataclass(frozen=True)
class Lexicon:
    engine: Engine
    sessions: sessionmaker[Session]


def open_lexicon(path: Path) -> Result[Lexicon, LexiconError]:
    if not path.exists():
        return Result.err(LexiconMissing(path))
    engine = make_engine(path, read_only=True)
    sessions = make_session_factory(engine)
    try:
        with sessions() as session:
            found = session.scalar(select(Meta.value).where(Meta.key == "schema_version"))
    except DatabaseError as e:
        engine.dispose()
        return Result.err(NotALexicon(path, str(e.orig)))
    if found is None or int(found) != SCHEMA_VERSION:
        engine.dispose()
        return Result.err(SchemaMismatch(int(found or 0), SCHEMA_VERSION, version("harald")))
    return Result.ok(Lexicon(engine, sessions))
