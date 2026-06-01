"""Pure calculation core: no I/O, no argument parsing.

All functions here are side-effect free and raise typed exceptions
so that callers (CLI, tests, future APIs) can handle errors uniformly.
"""

from __future__ import annotations

from typing import Callable, Dict


class CalculationError(Exception):
    """Base class for all calculation related errors."""


class InvalidOperandError(CalculationError):
    """Raised when an operand cannot be parsed as a number."""


class UnsupportedOperatorError(CalculationError):
    """Raised when the operator is not registered."""


class DivisionByZeroError(CalculationError):
    """Raised when dividing by zero."""


Operation = Callable[[float, float], float]

OPERATIONS: Dict[str, Operation] = {}


def register_operation(symbol: str, func: Operation) -> None:
    """Register a binary operation under the given symbol."""
    if not isinstance(symbol, str) or not symbol:
        raise ValueError("operator symbol must be a non-empty string")
    if not callable(func):
        raise ValueError("operation must be callable")
    OPERATIONS[symbol] = func


def _add(a: float, b: float) -> float:
    return a + b


def _sub(a: float, b: float) -> float:
    return a - b


def _mul(a: float, b: float) -> float:
    return a * b


def _div(a: float, b: float) -> float:
    if b == 0:
        raise DivisionByZeroError("division by zero is not allowed")
    return a / b


register_operation("+", _add)
register_operation("-", _sub)
register_operation("*", _mul)
register_operation("/", _div)


def parse_operand(raw: str) -> float:
    """Parse a raw string into a float, raising InvalidOperandError on failure."""
    if raw is None:
        raise InvalidOperandError("operand is missing")
    text = str(raw).strip()
    if not text:
        raise InvalidOperandError("operand is empty")
    try:
        return float(text)
    except (TypeError, ValueError) as exc:
        raise InvalidOperandError(f"invalid operand: {raw!r}") from exc


def calculate(a: float, operator: str, b: float) -> float:
    """Apply the registered operation for `operator` to a and b.

    Raises UnsupportedOperatorError for unknown operators and
    DivisionByZeroError when dividing by zero.
    """
    if operator not in OPERATIONS:
        raise UnsupportedOperatorError(f"unsupported operator: {operator!r}")
    return OPERATIONS[operator](a, b)
