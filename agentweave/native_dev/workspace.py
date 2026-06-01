"""Isolated artifact storage and deterministic verification."""

from __future__ import annotations

import ast
import json
import shutil
from pathlib import Path
from typing import Any, Dict, Iterable, List


class ArtifactVault:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def resolve(self, relative: str) -> Path:
        candidate = (self.root / relative).resolve()
        if self.root not in candidate.parents and candidate != self.root:
            raise ValueError(f"拒绝写入工作区外路径: {relative}")
        return candidate

    def apply(self, artifacts: Iterable[Dict[str, Any]], source: str) -> List[Dict[str, str]]:
        manifest = []
        for artifact in artifacts:
            relative = str(artifact.get("path", "")).strip()
            if not relative:
                continue
            content = str(artifact.get("content", ""))
            target = self.resolve(relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            manifest.append(
                {
                    "path": relative,
                    "source": source,
                }
            )
        return manifest

    def files(self) -> List[str]:
        return sorted(
            str(path.relative_to(self.root))
            for path in self.root.rglob("*")
            if path.is_file() and not path.is_symlink()
        )

    def seed_from(self, previous: Path) -> None:
        """Start a new revision from a prior workspace without modifying it."""
        if not previous.is_dir() or previous.is_symlink():
            raise ValueError("上一轮工作区不存在或不安全")
        for source in previous.rglob("*"):
            if source.is_symlink():
                raise ValueError("上一轮工作区包含符号链接，无法安全继承")
            if source.is_file():
                target = self.resolve(str(source.relative_to(previous)))
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)

    def snapshot(self, max_chars: int = 16000) -> Dict[str, str]:
        """Bound the source context sent to the model while retaining file names."""
        result: Dict[str, str] = {}
        remaining = max_chars
        for relative in self.files():
            if remaining <= 0:
                result[relative] = "[内容超出上下文预算]"
                continue
            try:
                content = self.resolve(relative).read_text(encoding="utf-8")
            except (UnicodeError, OSError):
                result[relative] = "[非文本文件]"
                continue
            excerpt = content[:remaining]
            result[relative] = excerpt + ("\n[内容已截断]" if len(content) > len(excerpt) else "")
            remaining -= len(excerpt)
        return result


class VerificationSuite:
    def inspect(self, vault: ArtifactVault) -> Dict[str, Any]:
        checks: List[Dict[str, str]] = []
        for relative in vault.files():
            path = vault.resolve(relative)
            status, detail = "passed", "格式检查通过"
            try:
                if path.suffix == ".py":
                    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
                elif path.suffix == ".json":
                    json.loads(path.read_text(encoding="utf-8"))
            except (SyntaxError, json.JSONDecodeError) as exc:
                status, detail = "failed", str(exc)
            checks.append({"file": relative, "status": status, "detail": detail})
        return {
            "passed": bool(checks) and all(item["status"] == "passed" for item in checks),
            "checked_files": len(checks),
            "checks": checks,
        }
