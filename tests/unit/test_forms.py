from harald.build.forms import parse_forms


def _row(form: str, *tags: str, source: str | None = "conjugation") -> dict[str, object]:
    row: dict[str, object] = {"form": form, "tags": list(tags)}
    if source:
        row["source"] = source
    return row


def _slots(*rows: dict[str, object]) -> dict[str, str]:
    return {f.slot: f.form for f in parse_forms("x", "verb", rows).verb_forms}


def test_head_rows_become_principal_part_slots() -> None:
    slots = _slots(
        _row("läuft", "present", "singular", "third-person", source=None),
        _row("lief", "past", source=None),
        _row("gelaufen", "participle", "past", source=None),
        _row("sein", "auxiliary", source=None),
    )

    assert slots == {
        "pp.pres3sg": "läuft", "pp.pret": "lief", "pp.part2": "gelaufen", "pp.aux": "sein",
    }  # fmt: skip


def test_table_rows_map_to_tense_and_person() -> None:
    slots = _slots(
        _row("läufst", "indicative", "present", "second-person", "singular"),
        _row("ist gelaufen", "indicative", "perfect", "third-person", "singular",
             "multiword-construction"),
        _row("liefe", "subjunctive", "subjunctive-ii", "third-person", "singular"),
        _row("lauft", "imperative", "plural", "second-person"),
        _row("anrufe", "indicative", "present", "first-person", "singular",
             "subordinate-clause"),
    )  # fmt: skip

    assert slots == {
        "ind.pres.2sg": "läufst", "ind.perf.3sg": "ist gelaufen", "subj2.pret.3sg": "liefe",
        "imp.2pl": "lauft", "ind.pres.1sg.sub": "anrufe",
    }  # fmt: skip


def test_bookkeeping_duplicates_and_variants() -> None:
    parsed = parse_forms(
        "x",
        "verb",
        [
            _row("t", "table-tags"),
            _row("sein", "auxiliary", source=None),
            _row("sein", "auxiliary", source=None),
            _row("riefe an", "rare", "subjunctive", "subjunctive-ii", "first-person", "singular"),
        ],
    )

    assert [(f.slot, f.variant) for f in parsed.verb_forms] == [
        ("pp.aux", ""), ("subj2.pret.1sg", "rare")
    ]  # fmt: skip
    assert parsed.unmapped == ()


def test_unmappable_rows_are_recorded_but_still_indexed() -> None:
    parsed = parse_forms(
        "laufen",
        "verb",
        [
            _row("laufet", "dual", "indicative", "present"),
            _row("läufe", "error-unknown-tag", "indicative", "present"),
            _row("ruft an", "indicative", "present", "third-person", "plural", "plural"),
        ],
    )

    assert [(u.tagset, u.form) for u in parsed.unmapped[:2]] == [
        ("dual indicative present", "laufet"),
        ("error-unknown-tag indicative present", "läufe"),
    ]
    assert parsed.index_forms[:2] == ("laufet", "läufe")


def test_index_skips_multiword_and_derivational_rows() -> None:
    parsed = parse_forms(
        "Hund",
        "noun",
        [
            _row("Hunde", "plural", source=None),
            _row("Hündin", "feminine", source=None),
            _row("ist gelaufen", "indicative", "perfect", "multiword-construction"),
            _row("ruft an!", "imperative", "second-person", "singular"),
        ],
    )

    assert parsed.index_forms == ("Hunde", "ruft an")
