import pytest

from harald.learning.answers import check_article, check_stammformen
from harald.text import answer_matches


@pytest.mark.parametrize(
    ("gender", "chosen", "correct"),
    [
        ("m", "der", True),
        ("f", "die", True),
        ("n", "das", True),
        ("m", "die", False),
        ("n", "der", False),
        ("nmf", "der", True),
        ("nmf", "die", True),
        ("nmf", "das", True),
        ("mn", "die", False),
    ],
)
def test_check_article(gender: str, chosen: str, correct: bool) -> None:
    assert check_article(gender, chosen).correct is correct


def test_every_gender_of_the_word_is_listed_as_accepted() -> None:
    assert check_article("nm", "die").accepted == ("das", "der")


ANRUFEN = {
    "infinitive": "anrufen",
    "pres3sg": "ruft an",
    "preterite": "rief an",
    "participle": "angerufen",
    "auxiliaries": ["haben"],
}
WRONG_ONLY_PRETERITE = ("ruft an", "rief", "hat angerufen")


@pytest.mark.parametrize(
    ("given", "expected", "matches"),
    [
        ("ruft an", "ruft an", True),
        ("  ruft   an ", "ruft an", True),
        ("Ruft an", "ruft an", False),
        ("fuehrt", "führt", True),
        ("führt", "führt", True),
        ("fuhr", "führt", False),
        ("Groesse", "Größe", True),
        ("Aerger", "Ärger", True),
        ("daürt", "dauert", True),
        ("ruft", "ruft an", False),
    ],
)
def test_answer_matches(given: str, expected: str, matches: bool) -> None:
    assert answer_matches(given, expected) is matches


def test_a_complete_correct_set_passes() -> None:
    check = check_stammformen(ANRUFEN, ("ruft an", "rief an", "hat angerufen"))

    assert check.correct
    assert [f.label for f in check.fields] == ["er/sie/es", "Präteritum", "Perfekt"]


def test_one_wrong_field_fails_the_card_and_names_the_expected_form() -> None:
    check = check_stammformen(ANRUFEN, WRONG_ONLY_PRETERITE)

    assert not check.correct
    assert [f.correct for f in check.fields] == [True, False, True]
    assert check.fields[1].expected == "rief an"


def test_perfekt_uses_the_auxiliary_as_it_stands_before_the_participle() -> None:
    sein = {**ANRUFEN, "participle": "gelaufen", "auxiliaries": ["sein"]}

    assert check_stammformen(sein, ("ruft an", "rief an", "ist gelaufen")).fields[2].correct
    assert not check_stammformen(sein, ("ruft an", "rief an", "hat gelaufen")).fields[2].correct


def test_a_verb_with_two_auxiliaries_accepts_either() -> None:
    both = {**ANRUFEN, "participle": "gestanden", "auxiliaries": ["haben", "sein"]}

    for perfect in ("hat gestanden", "ist gestanden"):
        assert check_stammformen(both, ("ruft an", "rief an", perfect)).fields[2].correct
    assert check_stammformen(both, ("ruft an", "rief an", "hat gestanden")).fields[2].expected == (
        "hat gestanden/ist gestanden"
    )


def test_umlaut_digraphs_are_accepted_in_a_stammformen_answer() -> None:
    content = {
        "pres3sg": "fährt um",
        "preterite": "fuhr um",
        "participle": "umgefahren",
        "auxiliaries": ["haben"],
    }

    assert check_stammformen(content, ("faehrt um", "fuhr um", "hat umgefahren")).correct
