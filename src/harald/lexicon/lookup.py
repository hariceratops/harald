from sqlalchemy import select
from sqlalchemy.orm import selectinload

from harald.lexicon import model
from harald.lexicon.db import Lexicon
from harald.lexicon.models import Entry, Headword, KeyHeadword, SearchKey
from harald.text import fold

_FULL_LIMIT = 3
_ALSO_LIMIT = 8


def lookup_de(lex: Lexicon, query: str) -> model.LookupResult:
    key = fold(" ".join(query.split()))
    with lex.sessions() as session:
        rows = session.execute(
            select(Headword, KeyHeadword.kind)
            .join(KeyHeadword, KeyHeadword.headword_id == Headword.id)
            .join(SearchKey, SearchKey.id == KeyHeadword.key_id)
            .where(SearchKey.lang == "de", SearchKey.key == key)
            .options(selectinload(Headword.entries).selectinload(Entry.senses))
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
        shown = tuple(_to_model(r[0]) for r in tier)
        also = tuple((r[0].lemma, r[0].pos) for r in ranked if r[0].id not in shown_ids)[
            :_ALSO_LIMIT
        ]
        return model.LookupResult(query, shown, also)


def _to_model(hw: Headword) -> model.Headword:
    return model.Headword(
        hw.lemma,
        hw.pos,
        tuple(
            model.Entry(e.gender, e.plural, tuple(s.gloss for s in e.senses)) for e in hw.entries
        ),
    )
