from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Result[T, E: Exception]:
    _ok: T | None = None
    _err: E | None = None

    @staticmethod
    def ok(value: T) -> "Result[T, Any]":
        return Result(_ok=value)

    @staticmethod
    def err(error: E) -> "Result[Any, E]":
        return Result(_err=error)

    @property
    def is_ok(self) -> bool:
        return self._err is None

    @property
    def is_err(self) -> bool:
        return self._err is not None

    def unwrap(self) -> T:
        if self._err is not None:
            raise RuntimeError(f"called unwrap on Err: {self._err}")
        return self._ok  # type: ignore[return-value]

    def unwrap_err(self) -> E:
        if self._err is None:
            raise RuntimeError("called unwrap_err on Ok")
        return self._err

    def map[T2](self, fn: Callable[[T], T2]) -> "Result[T2, E]":
        if self._err is not None:
            return Result(_err=self._err)
        return Result(_ok=fn(self._ok))  # type: ignore[arg-type]

    def map_err[E2: Exception](self, fn: Callable[[E], E2]) -> "Result[T, E2]":
        if self._err is not None:
            return Result(_err=fn(self._err))
        return Result(_ok=self._ok)

    def and_then[T2](self, fn: Callable[[T], "Result[T2, E]"]) -> "Result[T2, E]":
        if self._err is not None:
            return Result(_err=self._err)
        return fn(self._ok)  # type: ignore[arg-type]

    def unwrap_or(self, default: T) -> T:
        if self._err is not None:
            return default
        return self._ok  # type: ignore[return-value]
