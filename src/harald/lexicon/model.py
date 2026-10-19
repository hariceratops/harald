from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PrincipalParts:
    pres3sg: str | None
    pret: str | None
    part2: str | None
    auxiliaries: tuple[str, ...]


@dataclass(frozen=True)
class Entry:
    gender: str
    plural: str | None
    senses: tuple[str, ...]
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
