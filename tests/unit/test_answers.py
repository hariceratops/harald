import pytest

from harald.learning.answers import check_article


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
