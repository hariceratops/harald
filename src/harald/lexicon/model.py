from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PrincipalParts:
    pres3sg: str | None
    pret: str | None
    part2: str | None
    auxiliaries: tuple[str, ...]


@dataclass(frozen=True)
class Example:
    text: str
    translation: str | None
    quotation: bool
    ref: str | None


@dataclass(frozen=True)
class Sense:
    gloss: str
    labels: tuple[str, ...]
    examples: tuple[Example, ...]


@dataclass(frozen=True)
class Entry:
    gender: str
    plural: str | None
    senses: tuple[Sense, ...]
    ipa: str | None = None
    separable_prefix: str | None = None
    principal_parts: PrincipalParts | None = None
    # slot (e.g. "ind.pres.3sg") -> display forms, subordinate-clause slots left out
    conjugation: Mapping[str, tuple[str, ...]] = field(default_factory=dict)


@dataclass(frozen=True)
class Headword:
    lemma: str
    pos: str
    entries: tuple[Entry, ...]
    via_form: str | None = None


@dataclass(frozen=True)
class LookupResult:
    query: str
    shown: tuple[Headword, ...]
    also: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class SourceInfo:
    title: str
    licence: str
    attribution: str
    # the newest of the source's files, or "unknown"
    date: str


@dataclass(frozen=True)
class CoverageFigure:
    label: str
    numerator: int
    denominator: int

    @property
    def percent(self) -> float:
        return 100 * self.numerator / self.denominator if self.denominator else 0.0


@dataclass(frozen=True)
class LexiconInfo:
    schema_version: int
    sources: tuple[SourceInfo, ...]
    coverage: tuple[CoverageFigure, ...]
