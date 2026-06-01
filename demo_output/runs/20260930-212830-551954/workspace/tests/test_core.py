import math

import pytest

from calc.core import (
    CalculationError,
    DivisionByZeroError,
    InvalidOperandError,
    UnsupportedOperatorError,
    calculate,
    parse_operand,
    register_operation,
)


@pytest.mark.parametrize(
    "a,op,b,expected",
    [
        (1, "+", 2, 3),
        (-1, "+", 1, 0),
        (0, "+", 0, 0),
        (5, "-", 3, 2),
        (3, "-", 5, -2),
        (2, "*", 3, 6),
        (-2, "*", 3, -6),
        (0, "*", 100, 0),
        (6, "/", 3, 2),
        (1, "/", 4, 0.25),
        (-6, "/", 3, -2),
    ],
)
def test_calculate_basic(a, op, b, expected):
    assert calculate(a, op, b) == pytest.approx(expected)


@pytest.mark.parametrize("a,b", [(1, 0), (0, 0), (-1, 0), (1.5, 0.0)])
def test_division_by_zero(a, b):
    with pytest.raises(DivisionByZeroError):
        calculate(a, "/", b)


def test_division_by_zero_is_calculation_error():
    assert issubclass(DivisionByZeroError, CalculationError)


@pytest.mark.parametrize("op", ["%", "^", "", "++", "add"])
def test_unsupported_operator(op):
    with pytest.raises(UnsupportedOperatorError):
        calculate(1, op, 2)


@pytest.mark.parametrize("raw,expected", [("1", 1.0), (" 2.5 ", 2.5), ("-3", -3.0), ("1e3", 1000.0)])
def test_parse_operand_ok(raw, expected):
    assert parse_operand(raw) == pytest.approx(expected)


@pytest.mark.parametrize("raw", ["", "   ", "abc", "1,2", None, "--"])
def test_parse_operand_invalid(raw):
    with pytest.raises(InvalidOperandError):
        parse_operand(raw)


def test_register_operation_extends_registry():
    register_operation("**", lambda a, b: a ** b)
    try:
        assert calculate(2, "**", 10) == pytest.approx(1024)
    finally:
        from calc.core import OPERATIONS

        OPERATIONS.pop("**", None)


def test_register_operation_rejects_bad_input():
    with pytest.raises(ValueError):
        register_operation("", lambda a, b: a)
    with pytest.raises(ValueError):
        register_operation("@", "not-callable")


def test_float_precision_is_reasonable():
    assert math.isclose(calculate(0.1, "+", 0.2), 0.3, rel_tol=1e-9)
