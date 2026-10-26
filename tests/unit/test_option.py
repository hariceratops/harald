import pickle

import pytest

from harald.core.option import Option


def test_some_and_none() -> None:
    assert Option.some(3).is_some
    assert Option.none().is_none
    assert Option.some(None).is_some


def test_from_optional_keeps_falsy_values() -> None:
    assert Option.from_optional(None).is_none
    assert Option.from_optional(0).unwrap() == 0
    assert Option.from_optional("").unwrap() == ""


def test_unwrap_on_none_raises() -> None:
    with pytest.raises(RuntimeError):
        Option.none().unwrap()
    with pytest.raises(RuntimeError, match="no card"):
        Option.none().expect("no card")


def test_unwrap_or_and_else() -> None:
    assert Option.some(1).unwrap_or(9) == 1
    assert Option.none().unwrap_or(9) == 9
    assert Option.none().unwrap_or_else(lambda: 7) == 7


def test_map_and_then_chain() -> None:
    assert Option.some(2).map(lambda n: n + 1).unwrap() == 3
    assert Option.some(2).and_then(lambda n: Option.some(n * 5)).unwrap() == 10
    assert Option.none().map(lambda n: n + 1).is_none
    assert Option.some(2).and_then(lambda _: Option.none()).is_none


def test_map_or_variants() -> None:
    assert Option.some(2).map_or(0, lambda n: n * 2) == 4
    assert Option.none().map_or(0, lambda n: n * 2) == 0
    assert Option.none().map_or_else(lambda: -1, lambda n: n * 2) == -1


def test_or_else_filter_inspect() -> None:
    assert Option.none().or_else(lambda: Option.some(5)).unwrap() == 5
    assert Option.some(1).or_else(lambda: Option.some(5)).unwrap() == 1
    assert Option.some(4).filter(lambda n: n > 5).is_none
    assert Option.some(6).filter(lambda n: n > 5).is_some
    seen: list[int] = []
    Option.some(8).inspect(seen.append)
    Option.none().inspect(seen.append)
    assert seen == [8]


def test_flatten_and_zip() -> None:
    assert Option.some(Option.some(1)).flatten().unwrap() == 1
    assert Option.some(Option.none()).flatten().is_none
    assert Option.some(1).zip(Option.some("a")).unwrap() == (1, "a")
    assert Option.some(1).zip(Option.none()).is_none


def test_ok_or_bridges_to_result() -> None:
    assert Option.some(1).ok_or(ValueError("x")).unwrap() == 1
    err = ValueError("missing")
    assert Option.none().ok_or(err).unwrap_err() is err


def test_none_survives_pickling() -> None:
    assert pickle.loads(pickle.dumps(Option.none())).is_none
    assert pickle.loads(pickle.dumps(Option.some(0))).unwrap() == 0


def test_none_is_a_single_instance() -> None:
    assert Option.none() is Option.none()
    assert Option.from_optional(None) is Option.none()
