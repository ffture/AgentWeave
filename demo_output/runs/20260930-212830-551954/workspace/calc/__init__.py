"""calc: a small command line calculator package."""

from .core import (
    CalculationError,
    DivisionByZeroError,
    InvalidOperandError,
    UnsupportedOperatorError,
    OPERATIONS,
    calculate,
    register_operation,
)

__all__ = [
    "CalculationError",
    "DivisionByZeroError",
    "InvalidOperandError",
    "UnsupportedOperatorError",
    "OPERATIONS",
    "calculate",
    "register_operation",
]

__version__ = "1.1.0"
