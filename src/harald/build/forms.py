from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from harald.build.records import UnmappedRow, VerbFormRecord
from harald.core.option import Option

BOOKKEEPING = frozenset({"table-tags", "inflection-template", "class"})
DERIVATIONAL = frozenset({"diminutive", "alternative", "abbreviation", "canonical"})
VARIANT_MARKERS = frozenset({"formal", "rare", "nonstandard", "figuratively", "poetic"})
GENDERS = frozenset({"masculine", "feminine", "neuter"})
_PERSONS = {"first-person": "1", "second-person": "2", "third-person": "3"}
_NUMBERS = {"singular": "sg", "plural": "pl"}
_STRUCTURE = frozenset(
    {
        "indicative", "subjunctive", "imperative", "present", "preterite", "perfect",
        "pluperfect", "future", "future-i", "future-ii", "subjunctive-i", "subjunctive-ii",
        "multiword-construction", "subordinate-clause", "infinitive", "infinitive-zu",
        "participle", "past", "auxiliary",
    }
)  # fmt: skip
_DECLENSION = frozenset(
    {
        "nominative", "genitive", "dative", "accusative", "definite", "indefinite",
        "strong", "weak", "mixed", "with-article", "includes-article", "without-article",
        "predicative", "comparative", "superlative",
    }
)  # fmt: skip
KNOWN_TAGS = (
    BOOKKEEPING
    | DERIVATIONAL
    | VARIANT_MARKERS
    | GENDERS
    | _STRUCTURE
    | _DECLENSION
    | frozenset(_PERSONS)
    | frozenset(_NUMBERS)
)

_HEAD_SLOTS = {
    frozenset({"present", "singular", "third-person"}): "pp.pres3sg",
    frozenset({"past"}): "pp.pret",
    frozenset({"participle", "past"}): "pp.part2",
    frozenset({"auxiliary"}): "pp.aux",
}
_NONFINITE = {
    frozenset({"infinitive"}): "inf",
    frozenset({"infinitive", "infinitive-zu"}): "inf.zu",
    frozenset({"participle", "present"}): "part1",
    frozenset({"participle", "past"}): "part2",
    frozenset({"auxiliary"}): "aux",
    frozenset({"infinitive", "future-i"}): "inf.fut1",
    frozenset({"infinitive", "future-ii"}): "inf.fut2",
}
_TENSE_STEMS = {
    frozenset({"indicative", "present"}): "ind.pres",
    frozenset({"indicative", "preterite"}): "ind.pret",
    frozenset({"indicative", "perfect"}): "ind.perf",
    frozenset({"indicative", "pluperfect"}): "ind.plup",
    frozenset({"indicative", "future-i"}): "ind.fut1",
    frozenset({"indicative", "future-ii"}): "ind.fut2",
    frozenset({"subjunctive", "subjunctive-i"}): "subj1.pres",
    frozenset({"subjunctive", "perfect"}): "subj1.perf",
    frozenset({"subjunctive", "subjunctive-i", "perfect"}): "subj1.perf",
    frozenset({"subjunctive", "subjunctive-i", "future-i"}): "subj1.fut1",
    frozenset({"subjunctive", "subjunctive-i", "future-ii"}): "subj1.fut2",
    frozenset({"subjunctive", "subjunctive-ii"}): "subj2.pret",
    frozenset({"subjunctive", "pluperfect"}): "subj2.plup",
    frozenset({"subjunctive", "subjunctive-ii", "pluperfect"}): "subj2.plup",
    frozenset({"subjunctive", "subjunctive-ii", "future-i"}): "subj2.fut1",
    frozenset({"subjunctive", "subjunctive-ii", "future-ii"}): "subj2.fut2",
    frozenset({"imperative"}): "imp",
}


@dataclass(frozen=True)
class ParsedForms:
    verb_forms: tuple[VerbFormRecord, ...]
    index_forms: tuple[str, ...]
    unmapped: tuple[UnmappedRow, ...]


def parse_forms(word: str, pos: str, rows: Iterable[dict[str, Any]]) -> ParsedForms:
    verb_forms: list[VerbFormRecord] = []
    index_forms: list[str] = []
    unmapped: list[UnmappedRow] = []
    for row in rows:
        tags = frozenset(row.get("tags", ()))
        form = str(row["form"])
        if tags & BOOKKEEPING or tags & DERIVATIONAL or (tags and tags <= GENDERS):
            continue
        form = form.removesuffix("!")
        if _indexable(form, tags) and form not in index_forms:
            index_forms.append(form)
        variant = ",".join(sorted(tags & VARIANT_MARKERS))
        core = tags - VARIANT_MARKERS
        errored = any(t.startswith("error-") for t in tags)
        slot: Option[str] = Option.none()
        if pos == "verb" and not errored and core <= KNOWN_TAGS:
            slot = _head_slot(core) if "source" not in row else _table_slot(core)
        if slot.is_some:
            record = VerbFormRecord(slot.unwrap(), form, variant)
            if record not in verb_forms:
                verb_forms.append(record)
        elif errored or not tags <= KNOWN_TAGS or pos == "verb":
            unmapped.append(UnmappedRow(pos, " ".join(sorted(tags)), word, form))
    return ParsedForms(tuple(verb_forms), tuple(index_forms), tuple(unmapped))


def _indexable(form: str, tags: frozenset[str]) -> bool:
    if " " not in form:
        return bool(form)
    # split main-clause forms like "ruft an" are single words to the learner
    return "multiword-construction" not in tags and "infinitive-zu" not in tags


def _head_slot(core: frozenset[str]) -> Option[str]:
    return Option.from_optional(_HEAD_SLOTS.get(core))


def _table_slot(core: frozenset[str]) -> Option[str]:
    sub = "subordinate-clause" in core
    rest = core - {"subordinate-clause", "multiword-construction", "future"}
    persons = rest & _PERSONS.keys()
    numbers = rest & _NUMBERS.keys()
    structure = frozenset(rest - _PERSONS.keys() - _NUMBERS.keys())
    if not persons and not numbers:
        return Option.from_optional(_NONFINITE.get(structure))
    if len(persons) != 1 or len(numbers) != 1:
        return Option.none()
    stem = _TENSE_STEMS.get(structure)
    if stem is None:
        return Option.none()
    person = _PERSONS[next(iter(persons))] + _NUMBERS[next(iter(numbers))]
    if stem == "imp":
        return Option.some(f"imp.{person}") if person in ("2sg", "2pl") else Option.none()
    return Option.some(f"{stem}.{person}" + (".sub" if sub else ""))
