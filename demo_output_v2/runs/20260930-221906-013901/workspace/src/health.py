import time
from typing import Callable, Dict, Any


class HealthCheckError(Exception):
    pass


class DependencyTimeout(HealthCheckError):
    pass


def check_health(dependencies: Dict[str, Callable[[], bool]], timeout: float = 1.0) -> Dict[str, Any]:
    results: Dict[str, Any] = {}
    overall = True
    for name, probe in dependencies.items():
        start = time.monotonic()
        try:
            ok = bool(probe())
            elapsed = time.monotonic() - start
            if elapsed > timeout:
                results[name] = {"status": "timeout", "ok": False, "elapsed": elapsed}
                overall = False
            else:
                results[name] = {"status": "ok" if ok else "failed", "ok": ok, "elapsed": elapsed}
                overall = overall and ok
        except Exception as exc:  # noqa: BLE001
            elapsed = time.monotonic() - start
            results[name] = {"status": "error", "ok": False, "elapsed": elapsed, "error": str(exc)}
            overall = False
    return {"healthy": overall, "checks": results}
