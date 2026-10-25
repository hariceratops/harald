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
class ExampleRecord:
    text: str
    translation: str | None
    kind: str
    ref: str | None


@dataclass(frozen=True)
class SenseRecord:
    gloss: str
    labels: tuple[str, ...]
    examples: tuple[ExampleRecord, ...]


@dataclass(frozen=True)
class EntryRecord:
    lemma: str
    pos: str
    gender: str
    plural: str | None
    ipa: str | None
    senses: tuple[SenseRecord, ...]
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


@dataclass(frozen=True)
class DeExampleRecord:
    text: str
    ref: str | None


@dataclass(frozen=True)
class DeSenseRecord:
    # None marks a heading line such as "Plural »Bänder«:"
    sense_index: str | None
    gloss: str
    labels: tuple[str, ...]
    examples: tuple[DeExampleRecord, ...]


@dataclass(frozen=True)
class DeEntryRecord:
    lemma: str
    pos: str
    label: str
    senses: tuple[DeSenseRecord, ...]
