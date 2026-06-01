"""Persistent project memory and external knowledge ingestion."""

from __future__ import annotations

import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .client import ModelClient


class KnowledgeBase:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> List[Dict[str, Any]]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def add(self, entry: Dict[str, Any]) -> None:
        entries = self._load()
        enriched = dict(entry)
        enriched["created_at"] = datetime.now(timezone.utc).isoformat()
        entries.append(enriched)
        self.path.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")

    def recall(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        words = set(re.findall(r"[\w\u4e00-\u9fff]+", query.lower()))
        ranked = []
        for entry in self._load():
            text = json.dumps(entry, ensure_ascii=False).lower()
            score = sum(1 for word in words if word in text)
            ranked.append((score, entry))
        ranked.sort(key=lambda item: item[0], reverse=True)
        return [entry for score, entry in ranked[:limit] if score > 0]

    def learn_external(self, source: str, client: ModelClient) -> Dict[str, Any]:
        if source.startswith(("http://", "https://")):
            request = urllib.request.Request(source, headers={"User-Agent": "AgentWeave/1.0"})
            with urllib.request.urlopen(request, timeout=20) as response:
                raw = response.read(200_000).decode("utf-8", errors="replace")
        else:
            raw = Path(source).read_text(encoding="utf-8")
        prompt = (
            "请把下面的外部资料提炼为可复用的软件工程知识。返回字段："
            "title、summary、lessons（字符串数组）、tags（字符串数组）。\n\n" + raw[:30_000]
        )
        learned = client.complete_json("你是持续学习智能体。", prompt, "external_learning")
        learned["source"] = source
        self.add(learned)
        return learned
