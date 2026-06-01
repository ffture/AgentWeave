# Test Report

## Environment

- Python >= 3.9
- pytest >= 7.4, pytest-cov >= 4.1 (see `pyproject.toml` `[project.optional-dependencies].test`)

## How to run

```
pip install -e ".[test]"
pytest
```

`pytest.ini` and `pyproject.toml` both enable `--cov=calc --cov-report=term-missing`,
so a coverage table is printed on every run.

## Suites

| File | Scope |
| ---- | ----- |
| `tests/test_core.py` | parameterized math, parsing, registry, exception hierarchy |
| `tests/test_cli.py` | in-process CLI, JSON output, error paths, exit codes |
| `tests/test_acceptance.py` | subprocess `python -m calc` end-to-end |

## Covered edge cases

- Division by zero for `1/0`, `0/0`, `-1/0`, `1.5/0.0`.
- Invalid operands: empty string, whitespace, `abc`, `1,2`, `None`, `--`.
- Unsupported operators: `%`, `^`, empty, `++`, `add`.
- Wrong arity and mixed positional/`--expr` usage.
- Float precision via `math.isclose` for `0.1 + 0.2`.

## Status

All suites are expected to pass on a clean checkout. Re-run `pytest` after any
change to `calc/` and update this report if the suite set changes.
