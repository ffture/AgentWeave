"""Domain objects for the event-driven development lifecycle."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List


class Stage(str, Enum):
    CREATED = "created"
    ANALYZED = "analyzed"
    ORGANIZED = "organized"
    PLANNED = "planned"
    BUILT = "built"
    REVIEWED = "reviewed"
    EVOLVED = "evolved"
    LEARNED = "learned"
    COMPLETED = "completed"


_ALLOWED_TRANSITIONS = {
    Stage.CREATED: {Stage.ANALYZED},
    Stage.ANALYZED: {Stage.ORGANIZED},
    Stage.ORGANIZED: {Stage.PLANNED},
    Stage.PLANNED: {Stage.BUILT},
    Stage.BUILT: {Stage.REVIEWED},
    Stage.REVIEWED: {Stage.EVOLVED, Stage.LEARNED},
    Stage.EVOLVED: {Stage.LEARNED},
    Stage.LEARNED: {Stage.COMPLETED},
    Stage.COMPLETED: set(),
}


@dataclass(frozen=True)
class LifecycleEvent:
    sequence: int
    stage: Stage
    actor: str
    summary: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        value = asdict(self)
        value["stage"] = self.stage.value
        return value


class RunLedger:
    """Append-only state machine used as an auditable run history."""

    def __init__(self) -> None:
        self.stage = Stage.CREATED
        self._events: List[LifecycleEvent] = [
            LifecycleEvent(0, Stage.CREATED, "runtime", "创建隔离研发运行")
        ]

    def advance(self, stage: Stage, actor: str, summary: str) -> None:
        if stage not in _ALLOWED_TRANSITIONS[self.stage]:
            raise ValueError(f"非法生命周期迁移: {self.stage.value} -> {stage.value}")
        self.stage = stage
        self._events.append(LifecycleEvent(len(self._events), stage, actor, summary))

    def to_list(self) -> List[Dict[str, Any]]:
        return [event.to_dict() for event in self._events]

