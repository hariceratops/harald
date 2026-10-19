from dataclasses import dataclass


@dataclass(frozen=True)
class Entry:
    gender: str
    plural: str | None
    senses: tuple[str, ...]


@dataclass(frozen=True)
class Headword:
    lemma: str
    pos: str
    entries: tuple[Entry, ...]


@dataclass(frozen=True)
class LookupResult:
    query: str
    shown: tuple[Headword, ...]
    also: tuple[tuple[str, str], ...]
