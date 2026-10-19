from rich.console import Console, ConsoleOptions, Group, RenderResult
from rich.table import Table
from rich.text import Text

from harald.lexicon.model import Entry, Headword, LexiconInfo, LookupResult, PrincipalParts

_ARTICLES = {"m": "der", "f": "die", "n": "das"}
_NARROW_BELOW = 60
_AUX_FORMS = {"sein": "ist", "haben": "hat"}
_PERSONS = (
    ("1sg", "ich"), ("2sg", "du"), ("3sg", "er/sie/es"),
    ("1pl", "wir"), ("2pl", "ihr"), ("3pl", "sie/Sie"),
)  # fmt: skip
_DEFAULT_TENSES = (
    ("ind.pres", "Präsens"), ("ind.pret", "Präteritum"), ("ind.perf", "Perfekt"),
)  # fmt: skip
_FULL_TENSES = (
    *_DEFAULT_TENSES,
    ("ind.plup", "Plusquamperfekt"), ("ind.fut1", "Futur I"), ("ind.fut2", "Futur II"),
    ("subj1.pres", "Konjunktiv I"), ("subj1.perf", "Konj. I Perfekt"),
    ("subj1.fut1", "Konj. I Futur I"), ("subj1.fut2", "Konj. I Futur II"),
    ("subj2.pret", "Konjunktiv II"), ("subj2.plup", "Konj. II Plusq."),
    ("subj2.fut1", "Konj. II Futur I"), ("subj2.fut2", "Konj. II Futur II"),
)  # fmt: skip
_PERSON_COLUMN = 11
_TENSE_COLUMN = 23


def _pos_label(pos: str) -> str:
    return "proper noun" if pos == "name" else pos


def _title(hw: Headword, entry: Entry) -> str:
    if hw.pos == "noun" and entry.gender:
        return f"{'/'.join(_ARTICLES[g] for g in entry.gender)} {hw.lemma}"
    return hw.lemma


def _principal_parts_line(parts: PrincipalParts) -> str:
    auxiliary = "/".join(_AUX_FORMS.get(a, a) for a in parts.auxiliaries)
    participle = " ".join(x for x in (auxiliary, parts.part2) if x)
    return " / ".join(x for x in (parts.pres3sg, parts.pret, participle) if x)


class RenderConjugation:
    def __init__(self, entry: Entry, full: bool) -> None:
        self.entry = entry
        self.full = full

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        forms = self.entry.conjugation
        tenses = [
            (stem, name)
            for stem, name in (_FULL_TENSES if self.full else _DEFAULT_TENSES)
            if any(f"{stem}.{p}" in forms for p, _ in _PERSONS)
        ]
        per_row = max(1, (options.max_width - _PERSON_COLUMN) // _TENSE_COLUMN)
        for start in range(0, len(tenses), per_row):
            group = tenses[start : start + per_row]
            grid = Table.grid(padding=(0, 1))
            grid.add_column(no_wrap=True)
            for _ in group:
                grid.add_column(overflow="fold")
            grid.add_row("", *(Text(name, style="bold") for _, name in group))
            for person, label in _PERSONS:
                grid.add_row(
                    label, *(" / ".join(forms.get(f"{stem}.{person}", ())) for stem, _ in group)
                )
            yield grid
        imperative = [", ".join(forms[s]) for s in ("imp.2sg", "imp.2pl") if s in forms]
        if imperative:
            yield Text("Imperativ: " + "! / ".join(imperative) + "!")


class RenderHeadword:
    def __init__(self, hw: Headword, full_conjugation: bool = False) -> None:
        self.hw = hw
        self.full_conjugation = full_conjugation

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        narrow = options.max_width < _NARROW_BELOW
        label = _pos_label(self.hw.pos)
        if self.hw.via_form:
            yield Text(f"{self.hw.via_form} → {self.hw.lemma} ({label})", style="dim")
        for entry in self.hw.entries:
            title = Text(_title(self.hw, entry), style="bold")
            if narrow:
                yield title
                yield Text(label, style="dim")
                if entry.plural:
                    yield Text(f"Plural: {entry.plural}")
            else:
                line = Text.assemble(title, f"  {label}", style="")
                if entry.plural:
                    line.append(f"  Plural: {entry.plural}")
                yield line
            if entry.separable_prefix:
                stem = self.hw.lemma.removeprefix(entry.separable_prefix)
                yield Text(f"TRENNBAR {entry.separable_prefix}|{stem}", style="bold")
            if entry.principal_parts:
                yield Text(_principal_parts_line(entry.principal_parts))
            senses = Table.grid(padding=(0, 1))
            senses.add_column(justify="right", no_wrap=True)
            senses.add_column(ratio=1, overflow="fold")
            for i, gloss in enumerate(entry.senses, 1):
                senses.add_row(f"{i}.", gloss)
            yield senses
            if entry.conjugation:
                yield RenderConjugation(entry, self.full_conjugation)
            yield Text("")


class RenderLookup:
    def __init__(self, result: LookupResult, full_conjugation: bool = False) -> None:
        self.result = result
        self.full_conjugation = full_conjugation

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        for hw in self.result.shown:
            yield RenderHeadword(hw, self.full_conjugation)
        if self.result.also:
            names = ", ".join(lemma for lemma, _ in self.result.also)
            yield Text(f"Also: {names}", style="dim")


def render_lookup(result: LookupResult, full_conjugation: bool = False) -> RenderLookup:
    return RenderLookup(result, full_conjugation)


def render_info(info: LexiconInfo) -> Group:
    lines = [Text(f"Lexicon schema {info.schema_version}"), Text("Sources", style="bold")]
    for s in info.sources:
        lines.append(Text(f"  {s.title}"))
        lines.append(Text(f"    {s.date}   {s.licence}"))
        lines.append(Text(f"    {s.attribution}", style="dim"))
    lines.append(Text("Coverage (informational)", style="bold"))
    for c in info.coverage:
        lines.append(Text(f"  {c.label}"))
        lines.append(Text(f"    {c.percent:.1f} % ({c.numerator}/{c.denominator})"))
    return Group(*lines)
