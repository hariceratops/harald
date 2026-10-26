import pytest

from harald.lexicon.fuzzy import fuzzy_deletes, max_distance, osa_within


def test_fuzzy_deletes_use_first_seven_characters() -> None:
    assert fuzzy_deletes("ab") == {"ab", "a", "b"}
    assert "verschl" in fuzzy_deletes("verschlimmbessern")
    assert "verschlimm" not in fuzzy_deletes("verschlimmbessern")


@pytest.mark.parametrize(
    ("a", "b", "k", "expected"),
    [
        ("band", "band", 1, 0),
        ("bnad", "band", 1, 1),
        ("schnel", "schnell", 1, 1),
        ("schnel", "schnelle", 2, 2),
        ("schnel", "schnelle", 1, None),
        ("abc", "xyz", 2, None),
        ("hund", "", 3, None),
    ],
)
def test_osa_within(a: str, b: str, k: int, expected: int | None) -> None:
    assert osa_within(a, b, k).to_optional() == expected


def test_max_distance_is_one_for_short_keys() -> None:
    assert (max_distance("band"), max_distance("hunde")) == (1, 2)
