from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from harald.core.result import Result


# A flag, not an object() sentinel: a sentinel loses its identity when pickled, and job
# results cross the build's process boundary.
@dataclass(frozen=True, slots=True)
class Option[T]:
    _value: T | None = None
    _is_some: bool = False

    @staticmethod
    def some(value: T) -> "Option[T]":
        return Option(_value=value, _is_some=True)

    @staticmethod
    def none() -> "Option[Any]":
        return _NONE

    @staticmethod
    def from_optional(value: T | None) -> "Option[T]":
        return _NONE if value is None else Option(_value=value, _is_some=True)

    @property
    def is_some(self) -> bool:
        return self._is_some

    @property
    def is_none(self) -> bool:
        return not self._is_some

    def unwrap(self) -> T:
        if not self._is_some:
            raise RuntimeError("called unwrap on None")
        return self._value  # type: ignore[return-value]

    def expect(self, msg: str) -> T:
        if not self._is_some:
            raise RuntimeError(msg)
        return self._value  # type: ignore[return-value]

    def unwrap_or(self, default: T) -> T:
        return self._value if self._is_some else default  # type: ignore[return-value]

    def unwrap_or_else(self, fn: Callable[[], T]) -> T:
        return self._value if self._is_some else fn()  # type: ignore[return-value]

    def map[T2](self, fn: Callable[[T], T2]) -> "Option[T2]":
        if not self._is_some:
            return _NONE
        return Option.some(fn(self._value))  # type: ignore[arg-type]

    def map_or[T2](self, default: T2, fn: Callable[[T], T2]) -> T2:
        return fn(self._value) if self._is_some else default  # type: ignore[arg-type]

    def map_or_else[T2](self, default_fn: Callable[[], T2], fn: Callable[[T], T2]) -> T2:
        return fn(self._value) if self._is_some else default_fn()  # type: ignore[arg-type]

    def and_then[T2](self, fn: Callable[[T], "Option[T2]"]) -> "Option[T2]":
        if not self._is_some:
            return _NONE
        return fn(self._value)  # type: ignore[arg-type]

    def or_else(self, fn: Callable[[], "Option[T]"]) -> "Option[T]":
        return self if self._is_some else fn()

    def filter(self, predicate: Callable[[T], bool]) -> "Option[T]":
        if self._is_some and predicate(self._value):  # type: ignore[arg-type]
            return self
        return _NONE

    def inspect(self, fn: Callable[[T], None]) -> "Option[T]":
        if self._is_some:
            fn(self._value)  # type: ignore[arg-type]
        return self

    def flatten[U](self: "Option[Option[U]]") -> "Option[U]":
        if not self._is_some:
            return _NONE
        return self._value  # type: ignore[return-value]

    def zip[T2](self, other: "Option[T2]") -> "Option[tuple[T, T2]]":
        if self._is_some and other._is_some:
            return Option.some((self._value, other._value))  # type: ignore[arg-type]
        return _NONE

    def ok_or[E: Exception](self, err: E) -> Result[T, E]:
        if self._is_some:
            return Result.ok(self._value)  # type: ignore[arg-type]
        return Result.err(err)


_NONE: Option[Any] = Option()
