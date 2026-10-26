import json

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from harald.core.option import Option
from harald.lexicon import model
from harald.lexicon.db import Lexicon
from harald.lexicon.fuzzy import fuzzy_deletes, max_distance, osa_within
from harald.lexicon.models import (
    DeEntry,
    DeSense,
    Entry,
    EnWord,
    FuzzyDelete,
    Headword,
    KeyEnWord,
    KeyHeadword,
    SearchKey,
    Sense,
    VerbForm,
)
from harald.text import fold

_FULL_LIMIT = 3
_ALSO_LIMIT = 8
_RESULT_CAP = 20


def _key_distances(session: Session, lang: str, key: str) -> dict[int, int]:
    limit = max_distance(key)
    candidates = session.execute(
        select(SearchKey.id, SearchKey.key)
        .join(FuzzyDelete, FuzzyDelete.key_id == SearchKey.id)
        .where(SearchKey.lang == lang, FuzzyDelete.d.in_(fuzzy_deletes(key)))
        .distinct()
    ).all()
    return {
        key_id: d.unwrap()
        for key_id, cand in candidates
        if (d := osa_within(key, cand, limit)).is_some
    }


_FULL_LOAD = (
    selectinload(Headword.entries).selectinload(Entry.senses).selectinload(Sense.examples),
    selectinload(Headword.entries).selectinload(Entry.verb_forms),
    selectinload(Headword.de_entries).selectinload(DeEntry.senses).selectinload(DeSense.examples),
)


def load_headword(lex: Lexicon, lemma: str, pos: str) -> Option[model.Headword]:
    with lex.sessions() as session:
        hw = session.scalar(
            select(Headword)
            .where(Headword.lemma == lemma, Headword.pos == pos)
            .options(*_FULL_LOAD)
        )
        if hw is None:
            return Option.none()
        return Option.some(_to_model(hw, False, lemma))


def lookup_en(lex: Lexicon, query: str) -> model.EnLookupResult:
    typed = " ".join(query.split())
    with lex.sessions() as session:
        distance = _key_distances(session, "en", fold(typed))
        if not distance:
            return model.EnLookupResult(query, ())
        rows = session.execute(
            select(EnWord, KeyEnWord.key_id)
            .join(KeyEnWord, KeyEnWord.en_word_id == EnWord.id)
            .where(KeyEnWord.key_id.in_(distance))
            .options(selectinload(EnWord.translations))
        ).all()
        ranked = sorted(
            ((distance[key_id], w) for w, key_id in rows), key=lambda m: (m[0], m[1].id)
        )
        best = ranked[0][0]
        shown = tuple(_en_word_model(w) for d, w in ranked if d == best)[:_RESULT_CAP]
        return model.EnLookupResult(query, shown)


def _en_word_model(w: EnWord) -> model.EnWord:
    # one group per distinct sense string, in source order
    by_sense: dict[str, list[model.GermanTranslation]] = {}
    for t in w.translations:
        by_sense.setdefault(t.sense, []).append(model.GermanTranslation(t.german, t.gender, t.note))
    return model.EnWord(
        w.word,
        w.pos,
        tuple(model.TranslationGroup(sense, tuple(words)) for sense, words in by_sense.items()),
    )


def lookup_de(lex: Lexicon, query: str) -> model.LookupResult:
    typed = " ".join(query.split())
    key = fold(typed)
    with lex.sessions() as session:
        distance = _key_distances(session, "de", key)
        if not distance:
            return model.LookupResult(query, (), ())
        rows = session.execute(
            select(Headword, KeyHeadword.kind, KeyHeadword.key_id)
            .join(KeyHeadword, KeyHeadword.headword_id == Headword.id)
            .where(KeyHeadword.key_id.in_(distance))
        ).all()
        # one entry per headword, keeping its best (distance, kind)
        best: dict[int, tuple[int, int, Headword]] = {}
        for hw, kind, key_id in rows:
            match = (distance[key_id], kind)
            if hw.id not in best or match < best[hw.id][:2]:
                best[hw.id] = (*match, hw)
        # proper nouns rank after common words at the same distance
        ranked = sorted(
            best.values(),
            key=lambda m: (m[0], m[2].pos == "name", m[1], -m[2].richness, m[2].lemma, m[2].pos),
        )[:_RESULT_CAP]
        first_dist, first_kind, first = ranked[0]
        tier = [
            m
            for m in ranked
            if (m[0], m[1], m[2].pos == "name") == (first_dist, first_kind, first.pos == "name")
        ][:_FULL_LIMIT]
        shown_ids = [m[2].id for m in tier]
        loaded = {
            hw.id: hw
            for hw in session.scalars(
                select(Headword).where(Headword.id.in_(shown_ids)).options(*_FULL_LOAD)
            )
        }
        shown = tuple(_to_model(loaded[m[2].id], m[0] == 0 and m[1] == 1, typed) for m in tier)
        also = tuple((m[2].lemma, m[2].pos) for m in ranked if m[2].id not in shown_ids)[
            :_ALSO_LIMIT
        ]
        return model.LookupResult(query, shown, also)


def _to_model(hw: Headword, via_form: bool, typed: str) -> model.Headword:
    return model.Headword(
        hw.lemma,
        hw.pos,
        tuple(_entry_model(e) for e in hw.entries),
        tuple(_german_model(d) for d in hw.de_entries),
        via_form=typed if via_form else None,
    )


def _entry_model(e: Entry) -> model.Entry:
    slots = _display_forms(e.verb_forms)
    return model.Entry(
        e.gender,
        e.plural,
        tuple(_sense_model(s) for s in e.senses),
        e.ipa,
        e.separable_prefix,
        _principal_parts(slots) if slots else None,
        {s: f for s, f in slots.items() if not s.endswith(".sub")},
    )


def _german_model(d: DeEntry) -> model.GermanEntry:
    return model.GermanEntry(
        d.label,
        tuple(
            model.GermanSense(
                s.sense_index,
                s.gloss,
                tuple(json.loads(s.labels)),
                tuple(model.GermanExample(ex.text, ex.ref) for ex in s.examples),
            )
            for s in d.senses
        ),
    )


def _sense_model(s: Sense) -> model.Sense:
    return model.Sense(
        s.gloss,
        tuple(json.loads(s.labels)),
        tuple(
            model.Example(ex.text, ex.translation, ex.kind == "quotation", ex.ref)
            for ex in s.examples
        ),
    )


def _display_forms(rows: list[VerbForm]) -> dict[str, tuple[str, ...]]:
    by_slot: dict[str, list[VerbForm]] = {}
    for row in rows:
        by_slot.setdefault(row.slot, []).append(row)
    # variant forms (rare, formal ...) only stand in when a slot has nothing plain
    return {
        slot: tuple(r.form for r in group if not r.variant) or (group[0].form,)
        for slot, group in by_slot.items()
    }


def _principal_parts(slots: dict[str, tuple[str, ...]]) -> model.PrincipalParts:
    def first(*names: str) -> Option[str]:
        return Option.from_optional(next((slots[n][0] for n in names if n in slots), None))

    aux = slots.get("pp.aux") or slots.get("aux", ())
    return model.PrincipalParts(
        first("pp.pres3sg", "ind.pres.3sg").to_optional(),
        first("pp.pret", "ind.pret.3sg").to_optional(),
        first("pp.part2", "part2").to_optional(),
        aux,
    )
