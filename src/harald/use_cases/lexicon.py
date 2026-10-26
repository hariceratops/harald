from harald.config import Config
from harald.core.option import Option
from harald.core.result import Result
from harald.lexicon import model
from harald.lexicon.db import open_lexicon
from harald.lexicon.errors import LexiconError
from harald.lexicon.info import load_info
from harald.lexicon.lookup import load_headword, lookup_de, lookup_en
from harald.lexicon.schema import SCHEMA_VERSION


class LookUpGerman:
    def __init__(self, config: Config) -> None:
        self._config = config

    def execute(self, query: str) -> Result[model.LookupResult, LexiconError]:
        opened = open_lexicon(self._config.lexicon)
        if opened.is_err:
            return Result.err(opened.unwrap_err())
        return Result.ok(lookup_de(opened.unwrap(), query))


class LookUpEnglish:
    def __init__(self, config: Config) -> None:
        self._config = config

    def execute(self, query: str) -> Result[model.EnLookupResult, LexiconError]:
        opened = open_lexicon(self._config.lexicon)
        if opened.is_err:
            return Result.err(opened.unwrap_err())
        return Result.ok(lookup_en(opened.unwrap(), query))


class LoadHeadword:
    def __init__(self, config: Config) -> None:
        self._config = config

    def execute(self, lemma: str, pos: str) -> Result[Option[model.Headword], LexiconError]:
        opened = open_lexicon(self._config.lexicon)
        if opened.is_err:
            return Result.err(opened.unwrap_err())
        return Result.ok(load_headword(opened.unwrap(), lemma, pos))


class QueryLexiconInfo:
    def __init__(self, config: Config) -> None:
        self._config = config

    def execute(self) -> Result[model.LexiconInfo, LexiconError]:
        opened = open_lexicon(self._config.lexicon)
        if opened.is_err:
            return Result.err(opened.unwrap_err())
        return Result.ok(load_info(opened.unwrap(), SCHEMA_VERSION))
