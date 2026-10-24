from harald.lexicon import model
from harald.lexicon.db import Lexicon
from harald.lexicon.info import load_info
from harald.lexicon.lookup import lookup_de
from harald.lexicon.schema import SCHEMA_VERSION


class LookUpGerman:
    def __init__(self, lex: Lexicon) -> None:
        self._lex = lex

    def execute(self, query: str) -> model.LookupResult:
        return lookup_de(self._lex, query)


class QueryLexiconInfo:
    def __init__(self, lex: Lexicon) -> None:
        self._lex = lex

    def execute(self) -> model.LexiconInfo:
        return load_info(self._lex, SCHEMA_VERSION)
