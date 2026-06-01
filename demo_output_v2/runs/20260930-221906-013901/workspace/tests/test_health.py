import time
import pytest

from src.health import check_health


def test_health_all_ok():
    result = check_health({"db": lambda: True, "cache": lambda: True})
    assert result["healthy"] is True
    assert result["checks"]["db"]["status"] == "ok"


def test_health_dependency_failure():
    result = check_health({"db": lambda: True, "cache": lambda: False})
    assert result["healthy"] is False
    assert result["checks"]["cache"]["status"] == "failed"


def test_health_timeout():
    def slow():
        time.sleep(0.05)
        return True

    result = check_health({"slow": slow}, timeout=0.001)
    assert result["healthy"] is False
    assert result["checks"]["slow"]["status"] == "timeout"


def test_health_exception():
    def boom():
        raise RuntimeError("down")

    result = check_health({"svc": boom})
    assert result["healthy"] is False
    assert result["checks"]["svc"]["status"] == "error"
    assert "down" in result["checks"]["svc"]["error"]
