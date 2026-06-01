# Design

## Goals

- Provide a small, dependency-free command line calculator.
- Keep math logic pure and independently testable.
- Make error handling explicit and uniform.

## Layers

1. `calc/core.py` - pure functions and the operation registry. No I/O.
2. `calc/cli.py` - argument parsing, error formatting, exit codes.
3. `calc/__main__.py` - enables `python -m calc`.

## Operation registry

Operations are stored in `OPERATIONS: Dict[str, Callable[[float, float], float]]`.
New operators can be added with `register_operation(symbol, func)` without
touching the CLI or the dispatcher, satisfying the open/closed principle.

## Exception hierarchy

- `CalculationError` - base class for all calculation failures.
- `InvalidOperandError` - operand could not be parsed as a number.
- `UnsupportedOperatorError` - operator not present in the registry.
- `DivisionByZeroError` - divisor is zero.

The CLI catches `CalculationError` and maps it to exit code 2, printing a
human readable message to stderr.

## Exit codes

| Code | Meaning |
| ---- | ------- |
| 0 | success |
| 2 | calculation or usage error |

## Testing strategy

- `tests/test_core.py` - parameterized unit tests for math, parsing, registry.
- `tests/test_cli.py` - in-process CLI tests using `capsys`.
- `tests/test_acceptance.py` - subprocess tests against `python -m calc`.
- Coverage is enabled via `pytest.ini` and `pyproject.toml`.
