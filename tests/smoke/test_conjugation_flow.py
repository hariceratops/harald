import subprocess
import sys

import pytest

from tests.conftest import Workspace


def _lookup(ws: Workspace, *args: str, columns: int = 80) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "harald", "--config", str(ws.config_file), "lookup", *args],
        capture_output=True,
        text=True,
        env={"COLUMNS": str(columns), "PATH": "", "HOME": str(ws.root)},
    )


def test_inflected_form_finds_the_lemma_with_principal_parts(built: Workspace) -> None:
    res = _lookup(built, "lief")

    assert res.returncode == 0, res.stderr
    assert "lief → laufen (verb)" in res.stdout
    assert "läuft / lief / ist gelaufen" in res.stdout


def test_form_only_listed_in_the_conjugation_table_also_resolves(built: Workspace) -> None:
    assert "laufen (verb)" in _lookup(built, "liefst").stdout


@pytest.mark.parametrize("columns", [40, 60, 80, 100])
def test_conjugation_fits_the_terminal_and_loses_nothing(built: Workspace, columns: int) -> None:
    res = _lookup(built, "laufen", "--conj", columns=columns)

    assert res.returncode == 0, res.stderr
    assert max(len(line) for line in res.stdout.splitlines()) <= columns
    flat = "".join(res.stdout.split())
    for form in ("laufe", "läufst", "liefst", "bistgelaufen", "seidgelaufen", "liefet"[:5],
                 "Imperativ:lauf,laufe!/lauft!"):  # fmt: skip
        assert form in flat


def test_default_conjugation_omits_rare_tenses(built: Workspace) -> None:
    out = _lookup(built, "laufen").stdout

    assert "Perfekt" in out
    assert "Konjunktiv" not in out
    assert "Konjunktiv II" in _lookup(built, "laufen", "--conj").stdout


def test_separable_verb_is_shown_split(built: Workspace) -> None:
    out = _lookup(built, "anrufen", columns=40).stdout

    assert "TRENNBAR an|rufen" in out
    assert "ruft an / rief an / hat angerufen" in out
    assert "rufe an" in out
    assert "anrufe\n" not in out and "anrufe " not in out
    assert max(len(line) for line in out.splitlines()) <= 40


def test_unmapped_tag_sets_are_recorded_in_the_lexicon(built: Workspace) -> None:
    import sqlite3

    con = sqlite3.connect(built.config.lexicon)
    rows = con.execute(
        "SELECT pos, tagset, occurrences, example_word FROM unmapped_tagset"
    ).fetchall()
    con.close()

    assert ("verb", "dual indicative present", 1, "laufen") in rows
    assert ("verb", "error-unknown-tag indicative present", 1, "laufen") in rows
