from harald.build.errors import BuildError
from harald.build.prune import Prunable, prunable, prune_sources
from harald.config import Config
from harald.core.result import Result
from harald.lexicon.errors import LexiconError
from harald.use_cases.lexicon import QueryLexiconInfo


class PruneSources:
    def __init__(self, config: Config) -> None:
        self._config = config

    def plan(self) -> Result[list[Prunable], LexiconError]:
        # the sources are the only way to rebuild, so a lexicon that does not open keeps them
        opened = QueryLexiconInfo(self._config).execute()
        if opened.is_err:
            return Result.err(opened.unwrap_err())
        return Result.ok(prunable(self._config.sources_dir))

    def execute(self) -> Result[int, BuildError | LexiconError]:
        opened = QueryLexiconInfo(self._config).execute()
        if opened.is_err:
            return Result.err(opened.unwrap_err())
        # Result is invariant, so the identity map widens the error to the union
        return prune_sources(self._config).map_err(lambda e: e)
