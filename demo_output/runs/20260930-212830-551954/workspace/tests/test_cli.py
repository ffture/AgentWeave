import json

import pytest

from calc.cli import run


@pytest.mark.parametrize(
    "argv,expected",
    [
        (["1", "+", "2"], "3.0"),
        (["6", "/", "3"], "2.0"),
        (["2", "*", "3"], "6.0"),
        (["5", "-", "8"], "-3.0"),
    ],
)
def test_cli_positional(capsys, argv, expected):
    code = run(argv)
    out = capsys.readouterr().out.strip()
    assert code == 0
    assert out == expected


def test_cli_expr_form(capsys):
    code = run(["--expr", "1 + 2"])
    out = capsys.readouterr().out.strip()
    assert code == 0
    assert out == "3.0"


def test_cli_json_output(capsys):
    code = run(["1", "+", "2", "--json"])
    out = capsys.readouterr().out.strip()
    assert code == 0
    payload = json.loads(out)
    assert payload["result"] == pytest.approx(3.0)
    assert payload["operator"] == "+"


def test_cli_division_by_zero(capsys):
    code = run(["1", "/", "0"])
    captured = capsys.readouterr()
    assert code == 2
    assert "division by zero" in captured.err


def test_cli_invalid_operand(capsys):
    code = run(["abc", "+", "1"])
    captured = capsys.readouterr()
    assert code == 2
    assert "invalid operand" in captured.err


def test_cli_unsupported_operator(capsys):
    code = run(["1", "%", "2"])
    captured = capsys.readouterr()
    assert code == 2
    assert "unsupported operator" in captured.err


def test_cli_wrong_arity(capsys):
    code = run(["1", "+"])
    captured = capsys.readouterr()
    assert code == 2
    assert "three tokens" in captured.err


def test_cli_rejects_mixed_input(capsys):
    code = run(["1", "+", "2", "--expr", "1 + 2"])
    captured = capsys.readouterr()
    assert code == 2
    assert "not both" in captured.err
