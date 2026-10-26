import pytest

from harald.core.result import Result


def test_ok_and_err() -> None:
    assert Result.ok(1).is_ok
    assert Result.err(ValueError("x")).is_err


def test_unwrap_on_wrong_arm_raises() -> None:
    with pytest.raises(RuntimeError):
        Result.err(ValueError("x")).unwrap()
    with pytest.raises(RuntimeError):
        Result.ok(1).unwrap_err()


def test_map_and_then_skip_errors() -> None:
    err = ValueError("x")
    assert Result.ok(2).map(lambda n: n + 1).unwrap() == 3
    assert Result.err(err).map(lambda n: n + 1).unwrap_err() is err
    assert Result.ok(2).and_then(lambda n: Result.ok(n * 5)).unwrap() == 10
    assert Result.err(err).and_then(lambda n: Result.ok(n * 5)).unwrap_err() is err


def test_map_err_and_unwrap_or() -> None:
    assert Result.err(ValueError("x")).map_err(lambda e: KeyError(str(e))).is_err
    assert Result.ok(1).map_err(lambda e: KeyError(str(e))).unwrap() == 1
    assert Result.err(ValueError("x")).unwrap_or(9) == 9
    assert Result.ok(1).unwrap_or(9) == 1


def test_ok_none_is_still_ok() -> None:
    assert Result.ok(None).is_ok
