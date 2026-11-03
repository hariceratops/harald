from collections.abc import Mapping
from dataclasses import dataclass, field

PERSONS = (
    ("1sg", "ich"), ("2sg", "du"), ("3sg", "er/sie/es"),
    ("1pl", "wir"), ("2pl", "ihr"), ("3pl", "sie/Sie"),
)  # fmt: skip
TENSES = (
    ("ind.pres", "Präsens"), ("ind.pret", "Präteritum"), ("ind.perf", "Perfekt"),
    ("ind.plup", "Plusquamperfekt"), ("ind.fut1", "Futur I"), ("ind.fut2", "Futur II"),
    ("subj1.pres", "Konjunktiv I"), ("subj1.perf", "Konj. I Perfekt"),
    ("subj1.fut1", "Konj. I Futur I"), ("subj1.fut2", "Konj. I Futur II"),
    ("subj2.pret", "Konjunktiv II"), ("subj2.plup", "Konj. II Plusq."),
    ("subj2.fut1", "Konj. II Futur I"), ("subj2.fut2", "Konj. II Futur II"),
)  # fmt: skip


@dataclass(frozen=True)
class PrincipalParts:
    pres3sg: str | None
    pret: str | None
    part2: str | None
    auxiliaries: tuple[str, ...]


@dataclass(frozen=True)
class KnownWord:
    lemma: str
    pos: str
    inflected: bool


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
class GermanExample:
    text: str
    ref: str | None


@dataclass(frozen=True)
class GermanSense:
    # the German edition's own numbering ("1", "1a"); None for a heading line
    index: str | None
    gloss: str
    labels: tuple[str, ...]
    examples: tuple[GermanExample, ...]


@dataclass(frozen=True)
class GermanEntry:
    label: str
    senses: tuple[GermanSense, ...]


@dataclass(frozen=True)
class Headword:
    lemma: str
    pos: str
    entries: tuple[Entry, ...]
    german: tuple[GermanEntry, ...] = ()
    via_form: str | None = None


@dataclass(frozen=True)
class LookupResult:
    query: str
    shown: tuple[Headword, ...]
    also: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class GermanTranslation:
    german: str
    gender: str
    note: str | None


@dataclass(frozen=True)
class TranslationGroup:
    # the English sense the words translate; empty when the source names none
    sense: str
    words: tuple[GermanTranslation, ...]


@dataclass(frozen=True)
class EnWord:
    word: str
    pos: str
    groups: tuple[TranslationGroup, ...]


@dataclass(frozen=True)
class EnLookupResult:
    query: str
    shown: tuple[EnWord, ...]


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
