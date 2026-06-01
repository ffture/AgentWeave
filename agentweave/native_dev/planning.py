"""Deterministic scheduling for model-generated task graphs."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List


class TaskGraph:
    def __init__(self, tasks: Iterable[Dict[str, Any]]) -> None:
        self._tasks = {str(task.get("id")): dict(task) for task in tasks if task.get("id")}
        if not self._tasks:
            raise ValueError("任务计划不能为空")

    def ordered(self) -> List[Dict[str, Any]]:
        pending = dict(self._tasks)
        ordered: List[Dict[str, Any]] = []
        completed = set()
        while pending:
            ready = [
                task_id
                for task_id, task in pending.items()
                if set(map(str, task.get("dependencies", []))).issubset(completed)
            ]
            if not ready:
                unresolved = {task_id: task.get("dependencies", []) for task_id, task in pending.items()}
                raise ValueError(f"任务图存在循环或未知依赖: {unresolved}")
            for task_id in ready:
                ordered.append(pending.pop(task_id))
                completed.add(task_id)
        return ordered

