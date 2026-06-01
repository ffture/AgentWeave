"""DeepSeek and deterministic offline model adapters."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Protocol


class ModelClient(Protocol):
    def complete_json(self, system: str, prompt: str, schema_name: str) -> Dict[str, Any]:
        """Return a JSON object for one agent decision."""


def _extract_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("模型没有返回有效 JSON")
        value = json.loads(text[start : end + 1])
    if not isinstance(value, dict):
        raise ValueError("模型返回值必须是 JSON 对象")
    return value


class DeepSeekClient:
    """Small OpenAI-compatible adapter for the official DeepSeek endpoint."""

    def __init__(self) -> None:
        from dotenv import load_dotenv
        from openai import APIConnectionError, APITimeoutError, OpenAI

        # The project-local configuration is authoritative. This also prevents a
        # stale shell-level key from silently overriding a newly updated .env.
        load_dotenv(override=True)
        api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("请先在 .env 中填写 DEEPSEEK_API_KEY，或使用 --offline 演示模式")
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=120.0)
        self.connection_errors = (APIConnectionError, APITimeoutError)

    def complete_json(self, system: str, prompt: str, schema_name: str) -> Dict[str, Any]:
        messages = [
            {
                "role": "system",
                "content": system + "\n只返回一个合法 JSON 对象，不要使用 Markdown 代码块。",
            },
            {
                "role": "user",
                "content": prompt + "\n字符串中的换行、双引号和反斜杠必须严格进行 JSON 转义。",
            },
        ]
        for attempt in range(3):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    temperature=0.2,
                    max_tokens=512 if schema_name == "conversation_turn" else 8192,
                    response_format={"type": "json_object"},
                    messages=messages,
                )
            except Exception as exc:
                if isinstance(exc, self.connection_errors):
                    raise RuntimeError("无法连接 DeepSeek API，请检查网络、DNS 或代理设置") from None
                status_code = getattr(exc, "status_code", None)
                if status_code == 401:
                    raise RuntimeError("DeepSeek 认证失败：请检查 .env 中的 DEEPSEEK_API_KEY 是否有效") from None
                raise RuntimeError(f"DeepSeek 请求失败（HTTP {status_code or '未知'}）") from None
            try:
                return _extract_json(response.choices[0].message.content or "")
            except ValueError:
                if attempt == 2:
                    raise RuntimeError("DeepSeek 连续返回无法解析的 JSON，请重新运行本次任务") from None
                messages[1]["content"] += "\n上次输出无法解析。请重新生成更短、严格有效的 JSON。"
        raise RuntimeError("DeepSeek 没有返回结果")


class OfflineClient:
    """Deterministic model used for local demonstrations and automated tests."""

    def complete_json(self, system: str, prompt: str, schema_name: str) -> Dict[str, Any]:
        if schema_name == "conversation_turn":
            context = json.loads(prompt)
            message = str(context["message"])
            has_project = bool(context.get("current_project"))
            revising = has_project and any(word in message for word in ("刚才", "之前", "继续", "修改", "加上", "增加", "优化", "这个项目"))
            developing = any(word in message for word in ("开发", "实现", "做一个", "写一个", "创建", "搭建", "构建"))
            intent = "revise" if revising else "start" if developing else "chat"
            greeting = message.strip().rstrip("！!。.").lower() in {"你好", "您好", "嗨", "hi", "hello", "hey"}
            return {
                "intent": intent,
                "reply": ("你好！告诉我想做什么程序，或继续修改刚才的项目。" if greeting
                          else "我在。描述一下你想开发或修改的程序。") if intent == "chat" else "",
                "requirement": message if intent != "chat" else "",
            }
        fixtures = {
            "requirement_analysis": {
                "summary": "构建一个由多角色智能体协作完成的软件原型",
                "functional_requirements": ["接收自然语言需求", "自动生成可运行代码", "自动评审与重构"],
                "quality_requirements": ["结构清晰", "具备测试", "保留运行记录"],
                "constraints": ["优先使用 Python 标准库"],
                "acceptance_criteria": ["生成的 Python 文件语法正确", "生成测试文件", "产生演化报告"],
            },
            "team_design": {
                "agents": [
                    {"name": "Atlas", "role": "架构师", "mission": "设计系统结构并控制技术风险", "skills": ["architecture", "planning"]},
                    {"name": "Nova", "role": "开发工程师", "mission": "实现可运行的软件", "skills": ["python", "implementation"]},
                    {"name": "Sentry", "role": "质量工程师", "mission": "设计测试并审查质量", "skills": ["testing", "review"]},
                ]
            },
            "task_plan": {
                "tasks": [
                    {"id": "T1", "title": "设计方案", "agent": "Atlas", "description": "给出轻量架构", "dependencies": []},
                    {"id": "T2", "title": "实现程序", "agent": "Nova", "description": "实现命令行原型", "dependencies": ["T1"]},
                    {"id": "T3", "title": "编写测试", "agent": "Sentry", "description": "为核心逻辑编写测试", "dependencies": ["T2"]},
                ]
            },
            "task_execution": {
                "summary": "完成分配任务并输出实现产物",
                "artifacts": [
                    {"path": "app.py", "content": "def greet(name: str) -> str:\n    return f\"Hello, {name}!\"\n\nif __name__ == \"__main__\":\n    print(greet(\"AI Native World\"))\n"},
                    {"path": "test_app.py", "content": "from app import greet\n\ndef test_greet():\n    assert greet(\"Ada\") == \"Hello, Ada!\"\n"},
                ],
                "risks": [],
            },
            "quality_review": {
                "score": 72,
                "strengths": ["实现简洁", "包含自动测试"],
                "problems": ["输入校验不足"],
                "refactor_opportunities": ["为名称增加空值校验并补充边界测试"],
            },
            "refactor": {
                "summary": "主动完成健壮性重构",
                "artifacts": [
                    {"path": "app.py", "content": "def greet(name: str) -> str:\n    clean_name = name.strip()\n    if not clean_name:\n        raise ValueError(\"name cannot be empty\")\n    return f\"Hello, {clean_name}!\"\n\nif __name__ == \"__main__\":\n    print(greet(\"AI Native World\"))\n"},
                    {"path": "test_app.py", "content": "from app import greet\n\ndef test_greet():\n    assert greet(\" Ada \") == \"Hello, Ada!\"\n\ndef test_empty_name():\n    try:\n        greet(\"  \")\n        assert False\n    except ValueError:\n        pass\n"},
                ],
                "reason": "质量智能体主动发现输入边界缺陷",
            },
            "learning": {
                "lessons": ["小型原型也需要输入边界检查", "测试应覆盖正常路径和异常路径"],
                "tags": ["python", "quality", "refactoring"],
            },
            "external_learning": {
                "title": "外部知识摘要",
                "summary": "已提炼输入资料中的工程实践，可供后续任务检索复用。",
                "lessons": ["先定义验收标准，再选择实现方案"],
                "tags": ["external", "engineering"],
            },
        }
        if schema_name not in fixtures:
            raise KeyError(f"未知离线场景: {schema_name}")
        return fixtures[schema_name]
