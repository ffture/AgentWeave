# Interface

## CLI

```
calc <a> <operator> <b>
calc --expr "<a> <operator> <b>"
calc <a> <operator> <b> --json
```

- `<a>`, `<b>`: numbers accepted by Python `float()` (e.g. `1`, `-2.5`, `1e3`).
- `<operator>`: one of `+`, `-`, `*`, `/`.
- `--json`: emit a JSON object with keys `a`, `operator`, `b`, `result`.

Positional operands and `--expr` are mutually exclusive.

## Exit codes

- `0` success
- `2` calculation or usage error (message on stderr)

## Python API

```python
from calc.core import calculate, parse_operand, register_operation

calculate(1, "+", 2)          # 3
calculate(1, "/", 0)          # raises DivisionByZeroError
parse_operand("2.5")          # 2.5
register_operation("**", pow) # extend the registry
```

## Errors

All errors derive from `CalculationError`:

- `InvalidOperandError`
- `UnsupportedOperatorError`
- `DivisionByZeroError`
