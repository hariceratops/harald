from sqlalchemy import select
from sqlalchemy.orm import selectinload

from harald.lexicon import model
from harald.lexicon.db import Lexicon
from harald.lexicon.models import Entry, Headword, KeyHeadword, SearchKey, VerbForm
from harald.text import fold

_FULL_LIMIT = 3
_ALSO_LIMIT = 8


def lookup_de(lex: Lexicon, query: str) -> model.LookupResult:
    typed = " ".join(query.split())
    key = fold(typed)
    with lex.sessions() as session:
        rows = session.execute(
            select(Headword, KeyHeadword.kind)
            .join(KeyHeadword, KeyHeadword.headword_id == Headword.id)
            .join(SearchKey, SearchKey.id == KeyHeadword.key_id)
            .where(SearchKey.lang == "de", SearchKey.key == key)
            .options(
                selectinload(Headword.entries).selectinload(Entry.senses),
                selectinload(Headword.entries).selectinload(Entry.verb_forms),
            )
        ).all()
        # proper nouns rank after common words at the same distance
        ranked = sorted(
            rows, key=lambda r: (r[0].pos == "name", r[1], -r[0].richness, r[0].lemma, r[0].pos)
        )
        if not ranked:
            return model.LookupResult(query, (), ())
        first, first_kind = ranked[0]
        tier = [
            r
            for r in ranked
            if (r[0].pos == "name") == (first.pos == "name") and r[1] == first_kind
        ][:_FULL_LIMIT]
        shown_ids = {r[0].id for r in tier}
        shown = tuple(_to_model(r[0], r[1], typed) for r in tier)
        also = tuple((r[0].lemma, r[0].pos) for r in ranked if r[0].id not in shown_ids)[
            :_ALSO_LIMIT
        ]
        return model.LookupResult(query, shown, also)


def _to_model(hw: Headword, kind: int, typed: str) -> model.Headword:
    return model.Headword(
        hw.lemma,
        hw.pos,
        tuple(_entry_model(e) for e in hw.entries),
        via_form=typed if kind == 1 else None,
    )


def _entry_model(e: Entry) -> model.Entry:
    slots = _display_forms(e.verb_forms)
    return model.Entry(
        e.gender,
        e.plural,
        tuple(s.gloss for s in e.senses),
        e.separable_prefix,
        _principal_parts(slots) if slots else None,
        {s: f for s, f in slots.items() if not s.endswith(".sub")},
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
