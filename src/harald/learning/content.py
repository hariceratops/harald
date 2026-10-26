from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from harald.lexicon.model import Entry, Headword


@dataclass(frozen=True)
class WordHint:
    lemma: str
    pos: str
    discriminator: str


@dataclass(frozen=True)
class NewCard:
    card_type: str
    content: dict[str, Any]


@dataclass(frozen=True)
class Refusal:
    card_type: str
    missing: tuple[str, ...]


@dataclass(frozen=True)
class CardPlan:
    word_hint: WordHint
    cards: tuple[NewCard, ...]
    refusals: tuple[Refusal, ...] = ()


def _discriminator(pos: str, entry: Entry) -> str:
    if pos == "noun":
        return f"{entry.gender}|{entry.plural or ''}"
    if pos == "verb" and entry.principal_parts and entry.principal_parts.part2:
        return entry.principal_parts.part2
    return ""


def _first_translated_example(entry: Entry, sense_index: int) -> dict[str, str] | None:
    for ex in entry.senses[sense_index].examples:
        if ex.translation and not ex.quotation:
            return {"text": ex.text, "translation": ex.translation}
    return None


def plan_word_cards(
    headword: Headword,
    entry_index: int | None,
    en_senses: Sequence[int],
    de_senses: Sequence[tuple[int, int]],
) -> CardPlan:
    """Picks are positions: `en_senses` into the chosen entry's senses, `de_senses` as
    (German entry, sense) into `headword.german`."""
    entry = headword.entries[entry_index] if entry_index is not None else None
    gender = entry.gender if entry else ""
    hint = WordHint(
        headword.lemma, headword.pos, _discriminator(headword.pos, entry) if entry else ""
    )
    cards: list[NewCard] = []

    if entry is not None:
        for i in en_senses:
            sense = entry.senses[i]
            content: dict[str, Any] = {
                "lemma": headword.lemma,
                "pos": headword.pos,
                "gender": gender,
                "gloss": sense.gloss,
                "labels": list(sense.labels),
            }
            example = _first_translated_example(entry, i)
            if example:
                content["example"] = example
            cards.append(NewCard("meaning_de_en", content))
            cards.append(NewCard("meaning_en_de", dict(content)))

    for de_entry, i in de_senses:
        sense_de = headword.german[de_entry].senses[i]
        if sense_de.index is None:
            continue
        cards.append(
            NewCard(
                "meaning_de_de",
                {
                    "lemma": headword.lemma,
                    "pos": headword.pos,
                    "gender": gender,
                    "definition": sense_de.gloss,
                },
            )
        )
    return CardPlan(hint, tuple(cards))
