"""End-to-end acceptance tests exercising the CLI as a user would."""

import subprocess
import sys

import pytest


@pytest.mark.parametrize(
    "args,expected",
    [
        (["1", "+", "2"], "3.0"),
        (["10", "-", "4"], "6.0"),
        (["3", "*", "7"], "21.0"),
        (["9", "/", "3"], "3.0"),
    ],
)
def test_module_entrypoint(args, expected):
    proc = subprocess.run(
        [sys.executable, "-m", "calc", *args],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() == expected


def test_module_entrypoint_division_by_zero():
    proc = subprocess.run(
        [sys.executable, "-m", "calc", "1", "/", "0"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2
    assert "division by zero" in proc.stderr
