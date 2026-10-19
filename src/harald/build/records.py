from dataclasses import dataclass


@dataclass(frozen=True)
class VerbFormRecord:
    slot: str
    form: str
    variant: str


@dataclass(frozen=True)
class UnmappedRow:
    pos: str
    tagset: str
    word: str
    form: str


@dataclass(frozen=True)
class EntryRecord:
    lemma: str
    pos: str
    gender: str
    plural: str | None
    glosses: tuple[str, ...]
    translated_senses: int
    separable_prefix: str | None
    verb_forms: tuple[VerbFormRecord, ...]
    index_forms: tuple[str, ...]
    unmapped: tuple[UnmappedRow, ...]


@dataclass(frozen=True)
class FormOfRecord:
    form: str
    lemma: str
    pos: str
