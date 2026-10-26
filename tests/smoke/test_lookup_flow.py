import subprocess
import sys

from harald.lexicon.schema import SCHEMA_VERSION
from tests.conftest import Workspace


def _harald(ws: Workspace, *args: str, columns: int = 80) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "harald", "--config", str(ws.config_file), *args],
        capture_output=True,
        text=True,
        env={"COLUMNS": str(columns), "PATH": "", "HOME": str(ws.root)},
    )


def test_build_then_lookup_hund_fits_40_columns(workspace: Workspace) -> None:
    built = _harald(workspace, "build")
    assert built.returncode == 0, built.stderr

    res = _harald(workspace, "lookup", "Hund", columns=40)

    assert res.returncode == 0, res.stderr
    assert "der Hund" in res.stdout
    assert "Plural: Hunde" in res.stdout
    assert "1. dog (Canis familiaris)" in res.stdout
    assert "4. a mining cart" in res.stdout
    assert max(len(line) for line in res.stdout.splitlines()) <= 40


def test_lookup_without_a_build_refuses_with_exit_2(workspace: Workspace) -> None:
    res = _harald(workspace, "lookup", "Hund")

    assert res.returncode == 2
    assert "harald build" in res.stderr


def test_lookup_no_match_exits_1(workspace: Workspace) -> None:
    _harald(workspace, "build")

    assert _harald(workspace, "lookup", "Zzzzzz").returncode == 1


def test_lookup_does_not_import_heavy_modules(built: Workspace) -> None:
    code = (
        "import sys; from harald.cli import main; "
        f"main(['--config', {str(built.config_file)!r}, 'lookup', 'Hund']); "
        "bad = [m for m in ('textual', 'alembic', 'fsrs', 'harald.learning', 'harald.build') "
        "if m in sys.modules]; "
        "print('IMPORTED', bad)"
    )
    res = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)

    assert "IMPORTED []" in res.stdout, res.stdout + res.stderr


def test_lookup_typo_returns_schnell(workspace: Workspace) -> None:
    _harald(workspace, "build")

    res = _harald(workspace, "lookup", "schnel")

    assert res.returncode == 0, res.stderr
    assert "schnell" in res.stdout


def test_schema_mismatch_refuses_with_exit_2_naming_both_versions(workspace: Workspace) -> None:
    import sqlite3

    assert _harald(workspace, "build").returncode == 0
    con = sqlite3.connect(workspace.config.lexicon)
    con.execute("UPDATE meta SET value = '99' WHERE key = 'schema_version'")
    con.commit()
    con.close()

    res = _harald(workspace, "lookup", "Hund")

    assert res.returncode == 2
    assert "schema 99" in res.stderr
    assert f"needs schema {SCHEMA_VERSION}" in res.stderr
    assert "Harald" in res.stderr


def test_info_shows_sources_dates_attribution_and_coverage(workspace: Workspace) -> None:
    assert _harald(workspace, "build").returncode == 0

    res = _harald(workspace, "info", columns=40)

    assert res.returncode == 0
    assert "CC BY-SA 4.0" in res.stdout
    assert "Tatoeba contributors" in res.stdout
    assert "verbs with complete Stammformen" in res.stdout
    assert "2026" not in res.stdout and "unknown" in res.stdout


def test_lookup_shows_ipa_labels_and_examples(workspace: Workspace) -> None:
    _harald(workspace, "build")

    res = _harald(workspace, "lookup", "Hund", columns=80)

    assert res.returncode == 0, res.stderr
    assert "/hʊnt/" in res.stdout
    assert "[derogatory] person who is despicable" in res.stdout
    assert "Der Hund bellt. — The dog barks." in res.stdout
    assert "Der  Hundt lief  daron." in res.stdout
    assert "Anon., 1850" in res.stdout


def test_lookup_band_shows_german_definitions_and_untranslated_examples(
    workspace: Workspace,
) -> None:
    _harald(workspace, "build")

    res = _harald(workspace, "lookup", "Band", columns=40)

    assert res.returncode == 0, res.stderr
    out = res.stdout
    assert max(len(line) for line in out.splitlines()) <= 40
    assert out.count("German definitions (de.wiktionary)") == 1
    assert out.count("German examples (untranslated)") == 1
    definitions, examples = out.split("German examples (untranslated)")
    assert "[1a]" in definitions and "[colloquial] schmales Stück" in definitions
    assert "Plural »Bänder«:" in definitions
    assert "Sie trug ein Band im Haar." in examples
    assert "Gruppe von Musikern" not in examples


def test_lookup_german_only_word_shows_the_german_block(workspace: Workspace) -> None:
    _harald(workspace, "build")

    res = _harald(workspace, "lookup", "Fernweh", columns=80)

    assert res.returncode == 0, res.stderr
    assert "Fernweh" in res.stdout
    assert "[1] Sehnsucht nach der Ferne" in res.stdout
    assert "German examples" not in res.stdout
