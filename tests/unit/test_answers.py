from typing import Any

import pytest
from fsrs import Rating

from harald.learning.answers import (
    Known,
    MeaningGraded,
    NoArticleStored,
    TryAgain,
    check_conjugation,
    check_meaning,
    check_stammformen,
)
from harald.lexicon.model import KnownWord
from harald.text import answer_matches, fold

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


def _conjugation_card(*forms: str) -> dict[str, Any]:
    return {"slot": "ind.perf.1sg", "forms": list(forms)}


def test_conjugation_accepts_any_listed_form_and_labels_the_person() -> None:
    card = _conjugation_card("habe gefahren", "bin gefahren")

    for form in ("habe gefahren", "bin gefahren"):
        assert check_conjugation(card, form).correct
    check = check_conjugation(card, "habe gefahrn")
    assert not check.correct
    assert (check.label, check.expected) == ("ich", "habe gefahren/bin gefahren")


def test_conjugation_accepts_umlaut_digraphs_but_not_a_missing_prefix() -> None:
    card = {"slot": "ind.pres.2sg", "forms": ["fährst um"]}

    assert check_conjugation(card, "faehrst um").correct
    assert not check_conjugation(card, "fährst").correct


def test_a_reflexive_conjugation_also_accepts_the_pronoun_after_the_first_word() -> None:
    card = {"slot": "ind.perf.1sg", "forms": ["habe gefreut"], "reflexive": True}

    assert check_conjugation(card, "habe gefreut").correct
    assert check_conjugation(card, "habe mich gefreut").correct
    assert not check_conjugation(card, "habe dich gefreut").correct
    assert check_conjugation(card, "habe mich gefreut").expected == "habe gefreut"


def test_each_person_takes_its_own_reflexive_pronoun() -> None:
    wanted = {
        "1sg": "mich",
        "2sg": "dich",
        "3sg": "sich",
        "1pl": "uns",
        "2pl": "euch",
        "3pl": "sich",
    }
    for person, pronoun in wanted.items():
        card = {"slot": f"ind.pres.{person}", "forms": ["freue"], "reflexive": True}
        assert check_conjugation(card, f"freue {pronoun}").correct


def test_a_non_reflexive_conjugation_refuses_the_pronoun() -> None:
    card = {"slot": "ind.pres.1sg", "forms": ["koche"]}

    assert not check_conjugation(card, "koche mich").correct


def _noun(gender: str = "m", lemma: str = "Hund", pos: str = "noun") -> dict[str, Any]:
    return {"lemma": lemma, "pos": pos, "gender": gender}


def _lexicon(*words: tuple[str, str, str, bool]) -> Known:
    """A known() over (typed form, lemma, pos, inflected) rows, keyed the way the lookup folds."""

    def known(word: str) -> tuple[KnownWord, ...]:
        key = fold(" ".join(word.split()))
        return tuple(
            KnownWord(lemma, pos, infl) for form, lemma, pos, infl in words if fold(form) == key
        )

    return known


NOTHING_KNOWN = _lexicon()


def _graded(
    content: dict[str, Any],
    given: str,
    previous: str | None = None,
    first_try: str | None = None,
    known: Known = NOTHING_KNOWN,
) -> MeaningGraded:
    checked = check_meaning(content, given, first_try, previous, known)
    assert isinstance(checked, MeaningGraded)
    return checked


@pytest.mark.parametrize("given", ["", "   "])
def test_an_empty_answer_is_again(given: str) -> None:
    checked = _graded(_noun(), given)

    assert (checked.rating, checked.word) == (Rating.Again, "empty")


def test_the_right_word_with_the_right_article_is_good() -> None:
    checked = _graded(_noun(), "der Hund")

    assert (checked.rating, checked.word, checked.article) == (Rating.Good, "right", "right")
    assert checked.expected == "der Hund"


@pytest.mark.parametrize("given", ["Der Hund", "DER Hund", "  der   Hund "])
def test_the_article_is_read_in_any_case_and_spacing(given: str) -> None:
    assert _graded(_noun(), given).rating == Rating.Good


@pytest.mark.parametrize("given", ["die Hund", "ein Hund", "den Hund", "des Hund", "eines Hund"])
def test_a_wrong_article_is_hard(given: str) -> None:
    checked = _graded(_noun(), given)

    assert (checked.rating, checked.word, checked.article) == (Rating.Hard, "right", "wrong")


def test_all_twelve_articles_are_recognised_not_folded_into_the_word() -> None:
    for article in "der die das ein eine einen einem einer eines den dem des".split():
        assert _graded(_noun(), f"{article} Hund").word == "right"


def test_a_missing_article_is_hard() -> None:
    checked = _graded(_noun(), "Hund")

    assert (checked.rating, checked.article) == (Rating.Hard, "missing")


def test_any_of_the_words_genders_counts() -> None:
    band = _noun("mfn", "Band")

    assert [_graded(band, f"{a} Band").rating for a in ("der", "die", "das")] == [Rating.Good] * 3
    assert _graded(band, "ein Band").rating == Rating.Hard
    assert _graded(band, "der Band").expected == "der/die/das Band"


def test_a_wrong_article_twice_running_is_again() -> None:
    checked = _graded(_noun(), "die Hund", previous="ein Hund")

    assert (checked.rating, checked.repeated_article) == (Rating.Again, True)


def test_a_missing_article_after_a_wrong_one_is_again() -> None:
    assert _graded(_noun(), "Hund", previous="die Hund").rating == Rating.Again


def test_only_the_last_try_of_the_previous_answer_counts() -> None:
    assert _graded(_noun(), "die Hund", previous="Katze | die Hund").rating == Rating.Again
    assert _graded(_noun(), "die Hund", previous="die Hund | der Hund").rating == Rating.Hard


@pytest.mark.parametrize("previous", [None, "", "der Hund", "die Katze", "Katze"])
def test_a_previous_answer_that_was_not_a_wrong_article_does_not_escalate(
    previous: str | None,
) -> None:
    checked = _graded(_noun(), "die Hund", previous=previous)

    assert (checked.rating, checked.repeated_article) == (Rating.Hard, False)


def test_a_correct_article_after_a_wrong_one_is_good() -> None:
    assert _graded(_noun(), "der Hund", previous="die Hund").rating == Rating.Good


def test_a_wrong_word_is_again_whatever_the_article() -> None:
    checked = _graded(_noun(), "der Katze")

    assert (checked.rating, checked.word, checked.article) == (Rating.Again, "wrong", "not_asked")


def test_a_noun_without_gender_is_typed_alone() -> None:
    plain = _graded(_noun("", "Fernweh"), "Fernweh")

    assert (plain.rating, plain.article, plain.expected) == (Rating.Good, "not_asked", "Fernweh")


@pytest.mark.parametrize("given", ["der Fernweh", "das Fernweh", "ein Fernweh", "Der Fernweh"])
def test_an_article_on_a_noun_without_gender_is_refused(given: str) -> None:
    assert (
        check_meaning(_noun("", "Fernweh"), given, None, None, NOTHING_KNOWN) == NoArticleStored()
    )


def test_an_article_alone_on_a_noun_without_gender_is_a_wrong_word_not_a_refusal() -> None:
    assert _graded(_noun("", "Leute"), "die").word == "wrong"


def test_a_refusal_on_the_second_try_refuses_again() -> None:
    assert (
        check_meaning(_noun("", "Fernweh"), "das Fernweh", "Fernweh", None, NOTHING_KNOWN)
        == NoArticleStored()
    )


@pytest.mark.parametrize("given", ["Berlin", "das Berlin", "der Berlin", "ein Berlin"])
def test_a_proper_noun_ignores_the_article_entirely(given: str) -> None:
    checked = _graded(_noun("n", "Berlin", "name"), given, previous="der Berlin")

    assert (checked.rating, checked.article, checked.repeated_article) == (
        Rating.Good,
        "not_asked",
        False,
    )


def test_a_proper_noun_with_a_wrong_word_is_again() -> None:
    assert _graded(_noun("n", "Berlin", "name"), "das Bonn").rating == Rating.Again


def test_umlaut_digraphs_are_accepted_on_the_word() -> None:
    maedchen = _noun("n", "Mädchen")

    assert _graded(maedchen, "das Maedchen").rating == Rating.Good
    assert _graded(_noun("f", "Straße"), "die Strasse").rating == Rating.Good


def test_an_article_word_is_not_stripped_from_a_non_noun() -> None:
    schnell = {"lemma": "schnell", "pos": "adj", "gender": ""}

    assert _graded(schnell, "schnell").rating == Rating.Good
    assert _graded(schnell, "der schnell").rating == Rating.Again


def test_a_verb_may_be_typed_with_a_leading_sich() -> None:
    verb = {"lemma": "freuen", "pos": "verb", "gender": ""}

    assert _graded(verb, "sich freuen").rating == Rating.Good
    assert _graded(verb, "freuen").rating == Rating.Good


def test_sich_is_kept_when_the_lemma_starts_with_it() -> None:
    verb = {"lemma": "sich auf den Weg machen", "pos": "verb", "gender": ""}

    assert _graded(verb, "sich auf den Weg machen").rating == Rating.Good
    assert _graded(verb, "auf den Weg machen").rating == Rating.Again


def test_sich_is_not_dropped_from_a_noun() -> None:
    assert _graded(_noun("", "Fernweh"), "sich Fernweh").rating == Rating.Again


def test_the_second_try_caps_a_pass_at_hard() -> None:
    right = _graded(_noun(), "der Hund", first_try="Katze")
    wrong = _graded(_noun(), "Katze", first_try="Hnd")

    assert (right.rating, right.second_try) == (Rating.Hard, True)
    assert wrong.rating == Rating.Again


def test_the_first_try_is_not_a_second_try() -> None:
    assert _graded(_noun(), "der Hund").second_try is False


def _check(content: dict[str, Any], given: str, known: Known = NOTHING_KNOWN, **kw: Any) -> Any:
    return check_meaning(content, given, kw.get("first_try"), kw.get("previous"), known)


@pytest.mark.parametrize(
    ("lemma", "given", "slip"),
    [
        ("Hund", "Hnd", False),
        ("Hund", "Hunt", False),
        ("Hund", "Hudn", False),
        ("Hund", "Hunde", False),
        ("Tisch", "Tich", True),
        ("Tisch", "Tischh", True),
        ("Tisch", "Tosch", True),
        ("Tisch", "Tsich", True),
        ("Tisch", "Tsc", False),
        ("Tisch", "Tsichh", False),
        ("Fenster", "Fensler", True),
        ("Fenster", "Fenstar", True),
        ("Fenster", "Fensat", False),
        ("Fenster", "Fensa", False),
        ("Kühlschrank", "Kuehlschrnk", True),
        ("Kühlschrank", "Kuehlscrnk", True),
        ("Kühlschrank", "Kuehlscnk", False),
        ("Kühlschrank", "Kuehlschrnak", True),
        ("Zeitschrift", "Zietschrfit", True),
        ("Zeitschrift", "Zeitschrfit", True),
        ("Zeitschrift", "Zietschrft", True),
        ("Zeitschrift", "Zietschrfta", False),
    ],
)
def test_the_slip_allowance_follows_the_length_of_the_lemma(
    lemma: str, given: str, slip: bool
) -> None:
    checked = _graded(_noun("", lemma), given)

    assert (checked.word, checked.rating) == (
        ("slip", Rating.Good) if slip else ("wrong", Rating.Again)
    )


def test_a_slip_shows_the_correct_spelling() -> None:
    checked = _graded(_noun("f", "Straße"), "die Strase")

    assert (checked.word, checked.expected) == ("slip", "die Straße")


def test_a_slip_with_a_wrong_article_is_hard() -> None:
    assert _graded(_noun("m", "Tisch"), "die Tich").rating == Rating.Hard


def test_a_slip_that_is_itself_a_word_is_not_forgiven() -> None:
    schoen = {"lemma": "schön", "pos": "adj", "gender": ""}
    known = _lexicon(("schon", "schon", "adv", False))

    assert _graded(schoen, "schon", known=known).word == "wrong"


def test_a_slip_that_is_a_form_of_a_word_of_another_part_of_speech_is_not_forgiven() -> None:
    known = _lexicon(("Tische", "Tisch", "noun", True))
    adjective = {"lemma": "Tischen", "pos": "adj", "gender": ""}

    assert _graded(adjective, "Tische", known=known).word == "wrong"


def test_wrong_capitalisation_alone_is_a_slip_at_any_length() -> None:
    for lemma, given in (("Hund", "hund"), ("Ei", "ei"), ("Mädchen", "mädchen")):
        checked = _graded(_noun("", lemma), given)
        assert (checked.word, checked.rating) == ("slip", Rating.Good)


def test_capitalisation_plus_a_typo_is_two_slips() -> None:
    assert _graded(_noun("n", "Mädchen"), "madchen").word == "wrong"


def test_wrong_capitalisation_that_makes_another_lemma_is_again() -> None:
    known = _lexicon(("essen", "essen", "verb", False))

    checked = _graded(_noun("n", "Essen"), "Das essen", known=known)

    assert (checked.word, checked.rating) == ("other_case_word", Rating.Again)


def test_wrong_capitalisation_that_is_only_an_inflected_form_still_passes() -> None:
    known = _lexicon(("fliege", "fliegen", "verb", True))

    assert _graded(_noun("f", "Fliege"), "die fliege", known=known).word == "slip"


def test_another_word_of_the_same_part_of_speech_offers_a_retry() -> None:
    known = _lexicon(("Katze", "Katze", "noun", False))

    assert _check(_noun(), "der Katze", known) == TryAgain("noun", "H", 4)


def test_the_cue_is_the_first_letter_and_length_of_the_lemma_not_the_article() -> None:
    known = _lexicon(("Katze", "Katze", "noun", False))

    assert _check(_noun("n", "Mädchen"), "Katze", known) == TryAgain("noun", "M", 7)


def test_a_form_of_another_word_of_the_same_part_of_speech_offers_a_retry() -> None:
    known = _lexicon(("Katzen", "Katze", "noun", True))

    assert isinstance(_check(_noun(), "Katzen", known), TryAgain)


def test_a_word_of_another_part_of_speech_is_again_without_a_retry() -> None:
    known = _lexicon(("essen", "essen", "verb", False))

    checked = _graded(_noun(), "essen", known=known)

    assert (checked.word, checked.rating) == ("wrong", Rating.Again)


def test_a_form_of_the_cards_own_word_is_again_without_a_retry() -> None:
    known = _lexicon(("Hunde", "Hund", "noun", True))

    checked = _graded(_noun(), "Hunde", known=known)

    assert (checked.word, checked.rating) == ("wrong", Rating.Again)


def test_a_right_second_try_is_hard_and_a_wrong_one_is_again() -> None:
    known = _lexicon(("Katze", "Katze", "noun", False))

    right = _graded(_noun(), "der Hund", first_try="Katze", known=known)
    other = _graded(_noun(), "Katze", first_try="Katze", known=known)
    typo = _graded(_noun(), "Hnd", first_try="Katze", known=known)

    assert (right.rating, right.second_try) == (Rating.Hard, True)
    assert (other.rating, other.word) == (Rating.Again, "wrong")
    assert typo.rating == Rating.Again


def test_a_slip_on_the_second_try_is_hard() -> None:
    known = _lexicon(("Katze", "Katze", "noun", False))

    assert _graded(_noun("", "Tisch"), "Tich", first_try="Katze", known=known).rating == Rating.Hard


def test_the_previous_answer_is_judged_with_the_known_words() -> None:
    known = _lexicon(("Tich", "Tich", "noun", False))
    card = _noun("m", "Tisch")

    counted = _graded(card, "Tisch", previous="die Tich")
    not_counted = _graded(card, "Tisch", previous="die Tich", known=known)

    assert (counted.rating, counted.repeated_article) == (Rating.Again, True)
    assert (not_counted.rating, not_counted.repeated_article) == (Rating.Hard, False)
