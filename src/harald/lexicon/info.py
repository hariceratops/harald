from sqlalchemy import select

from harald.lexicon import model
from harald.lexicon.db import Lexicon
from harald.lexicon.models import BuildStat, Source, SourceFile

UNKNOWN_DATE = "unknown"
COVERAGE_LABELS = (
    ("coverage.stammformen", "verbs with complete Stammformen"),
    ("coverage.noun_gender", "nouns with a gender"),
    ("coverage.translated_example", "senses with a translated example"),
)


def load_info(lex: Lexicon, schema_version: int) -> model.LexiconInfo:
    with lex.sessions() as session:
        dates: dict[str, list[str]] = {}
        for name, date in session.execute(select(SourceFile.source, SourceFile.source_date)):
            dates.setdefault(name, []).append(date)
        sources = tuple(
            model.SourceInfo(
                s.title,
                s.licence,
                s.attribution,
                max((d for d in dates.get(s.name, ()) if d != UNKNOWN_DATE), default=UNKNOWN_DATE),
            )
            for s in session.scalars(select(Source).order_by(Source.name))
        )
        stats = {s.metric: s for s in session.scalars(select(BuildStat))}
    coverage = tuple(
        model.CoverageFigure(label, stats[metric].numerator, stats[metric].denominator or 0)
        for metric, label in COVERAGE_LABELS
        if metric in stats
    )
    return model.LexiconInfo(schema_version, sources, coverage)
