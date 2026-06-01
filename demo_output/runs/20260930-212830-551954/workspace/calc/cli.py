"""Command line interface for calc.

The CLI only parses arguments and formats output; all math lives in core.

Supported forms:
    calc 1 + 2
    calc 1 + 2 --json
    calc --expr "1 + 2"
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from .core import (
    CalculationError,
    calculate,
    parse_operand,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="calc",
        description="A simple command line calculator supporting + - * /",
    )
    parser.add_argument("operands", nargs="*", help="<a> <operator> <b>")
    parser.add_argument(
        "--expr",
        default=None,
        help="expression form, e.g. --expr \"1 + 2\"",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print the result as JSON",
    )
    return parser


def _tokens_from_args(args: argparse.Namespace) -> List[str]:
    if args.expr is not None:
        if args.operands:
            raise CalculationError("use either positional operands or --expr, not both")
        return args.expr.split()
    return list(args.operands)


def run(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        tokens = _tokens_from_args(args)
        if len(tokens) != 3:
            raise CalculationError(
                "expected exactly three tokens: <a> <operator> <b>"
            )
        left = parse_operand(tokens[0])
        operator = tokens[1]
        right = parse_operand(tokens[2])
        result = calculate(left, operator, right)
    except CalculationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({"a": left, "operator": operator, "b": right, "result": result}))
    else:
        print(result)
    return 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
