import json

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from harald.lexicon import model
from harald.lexicon.db import Lexicon
from harald.lexicon.fuzzy import fuzzy_deletes, max_distance, osa_within
from harald.lexicon.models import (
    DeEntry,
    DeSense,
    Entry,
    FuzzyDelete,
    Headword,
    KeyHeadword,
    SearchKey,
    Sense,
    VerbForm,
)
from harald.text import fold

_FULL_LIMIT = 3
_ALSO_LIMIT = 8
_RESULT_CAP = 20


def lookup_de(lex: Lexicon, query: str) -> model.LookupResult:
    typed = " ".join(query.split())
    key = fold(typed)
    limit = max_distance(key)
    with lex.sessions() as session:
        candidates = session.execute(
            select(SearchKey.id, SearchKey.key)
            .join(FuzzyDelete, FuzzyDelete.key_id == SearchKey.id)
            .where(SearchKey.lang == "de", FuzzyDelete.d.in_(fuzzy_deletes(key)))
            .distinct()
        ).all()
        distance = {
            key_id: d
            for key_id, cand in candidates
            if (d := osa_within(key, cand, limit)) is not None
        }
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
                select(Headword)
                .where(Headword.id.in_(shown_ids))
                .options(
                    selectinload(Headword.entries)
                    .selectinload(Entry.senses)
                    .selectinload(Sense.examples),
                    selectinload(Headword.entries).selectinload(Entry.verb_forms),
                    selectinload(Headword.de_entries)
                    .selectinload(DeEntry.senses)
                    .selectinload(DeSense.examples),
                )
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
    def first(*names: str) -> str | None:
        return next((slots[n][0] for n in names if n in slots), None)

    aux = slots.get("pp.aux") or slots.get("aux", ())
    return model.PrincipalParts(
        first("pp.pres3sg", "ind.pres.3sg"),
        first("pp.pret", "ind.pret.3sg"),
        first("pp.part2", "part2"),
        aux,
    )
