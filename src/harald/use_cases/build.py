from dataclasses import dataclass

from harald.build.errors import BuildError
from harald.build.run import BuildReport, build
from harald.config import Config
from harald.core.result import Result
from harald.lexicon.db import open_lexicon
from harald.lexicon.errors import LexiconError
from harald.lexicon.model import LexiconInfo
from harald.use_cases.lexicon import QueryLexiconInfo


@dataclass(frozen=True)
class BuildDone:
    report: BuildReport
    info: LexiconInfo


class BuildLexicon:
    def __init__(self, config: Config) -> None:
        self._config = config

    def execute(self, fetch: bool, force: bool) -> Result[BuildDone, BuildError | LexiconError]:
        built = build(self._config, fetch, force)
        if built.is_err:
            return Result.err(built.unwrap_err())
        # opened after the publish, so it reads what the build just left in place
        opened = open_lexicon(self._config.lexicon)
        if opened.is_err:
            return Result.err(opened.unwrap_err())
        return Result.ok(BuildDone(built.unwrap(), QueryLexiconInfo(opened.unwrap()).execute()))
