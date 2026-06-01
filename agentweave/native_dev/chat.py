"""Conversational front end for an ongoing software-development session."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .client import DeepSeekClient, OfflineClient
from .runtime import AgentWeaveRuntime


class ChatSession:
    def __init__(self, runtime: AgentWeaveRuntime) -> None:
        self.runtime = runtime
        self.last_run: Path | None = None
        self.history: list[dict[str, str]] = []

    def reset(self) -> str:
        self.last_run = None
        self.history.clear()
        return "已开启新话题。之前的产物仍保存在 runs 目录中。"

    def status(self) -> str:
        return f"当前项目：{self.last_run / 'workspace'}" if self.last_run else "还没有正在开发的项目。"

    def _model_identity(self) -> str:
        if isinstance(self.runtime.client, OfflineClient):
            return "当前是显式开启的离线模拟模式，没有调用 DeepSeek API。"
        if isinstance(self.runtime.client, DeepSeekClient):
            return f"当前使用 DeepSeek API，模型是 {self.runtime.client.model}。"
        return f"当前使用 {type(self.runtime.client).__name__} 模型适配器。"

    def handle(self, message: str) -> str:
        normalized = message.strip().lower()
        identity_question = any(phrase in normalized for phrase in (
            "什么模型", "哪个模型", "模型是什么", "你是谁", "是离线吗", "离线的吗",
            "是不是离线", "是离线模式吗", "你是deepseek", "你是 deepseek",
        ))
        project_summary = None
        if self.last_run is not None:
            report = json.loads((self.last_run / "run_report.json").read_text(encoding="utf-8"))
            project_summary = {
                "requirement": report.get("requirement"),
                "summary": report.get("analysis", {}).get("summary"),
                "files": sorted(str(path.relative_to(self.last_run / "workspace"))
                                for path in (self.last_run / "workspace").rglob("*") if path.is_file()),
            }
        decision = self.runtime.client.complete_json(
            "你是 AgentWeave 的对话助手，正常自然地和用户交流。"
            f"你的实际运行身份：{self._model_identity()}"
            "不要把内部的意图判断、协调器或智能体角色误称为底层模型。"
            "判断用户是在闲聊/提问，要求创建新软件，还是修改当前项目。"
            "intent 只能是 chat、start、revise；没有当前项目时不得选 revise。"
            "普通问候、含糊的感叹和对系统的提问都选 chat。"
            "用户询问当前日期或时间时，使用输入中的 current_local_time 回答。"
            "仅当用户明确要求做软件或修改软件时才启动开发。"
            "返回 intent、reply、requirement 三个字符串字段。"
            "开发时 requirement 要整合最近上下文，但不要虚构未确定的功能。",
            json.dumps(
                {
                    "message": message,
                    "current_local_time": datetime.now().astimezone().isoformat(timespec="minutes"),
                    "model_identity": self._model_identity(),
                    "current_project": str(self.last_run / "workspace") if self.last_run else None,
                    "current_project_summary": project_summary,
                    "recent_dialogue": self.history[-8:],
                },
                ensure_ascii=False,
            ),
            "conversation_turn",
        )
        intent = decision.get("intent")
        if intent not in {"chat", "start", "revise"}:
            intent = "chat"
        if identity_question:
            intent = "chat"
        if intent == "revise" and self.last_run is None:
            intent = "chat"
        reply = str(decision.get("reply") or "").strip()
        requirement = str(decision.get("requirement") or "").strip()
        if intent == "chat" or not requirement:
            if identity_question:
                reply = self._model_identity()
            reply = reply or "我在。你可以描述要开发的程序，或者问我目前项目的情况。"
            self._remember(message, reply)
            return reply

        print("助手> 正在处理，完成后会给你产物位置…", flush=True)
        run_dir = self.runtime.run(
            requirement,
            previous_run=self.last_run if intent == "revise" else None,
        )
        self.last_run = run_dir
        report = json.loads((run_dir / "run_report.json").read_text(encoding="utf-8"))
        count = report["metrics"]["files"]
        action = "已更新" if intent == "revise" else "已生成"
        reply = f"{action}项目（{count} 个文件）：{run_dir / 'workspace'}"
        self._remember(message, reply)
        return reply

    def _remember(self, message: str, reply: str) -> None:
        self.history.extend([{"role": "user", "content": message}, {"role": "assistant", "content": reply}])
        self.history = self.history[-12:]
