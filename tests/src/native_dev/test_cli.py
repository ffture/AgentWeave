import json
import os
import sys

import pytest

from agentweave.native_dev.chat import ChatSession
from agentweave.native_dev.cli import _utf8_terminal_input, interactive_loop
from agentweave.native_dev.client import DeepSeekClient, OfflineClient
from agentweave.native_dev.runtime import AgentWeaveRuntime


def test_interactive_mode_is_quiet_and_continues_project(tmp_path, monkeypatch, capsys):
    messages = iter(["你好", "开发一个问候程序", "给刚才的程序增加输入校验", "/exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(messages))

    assert interactive_loop(AgentWeaveRuntime(OfflineClient(), tmp_path)) == 0
    runs = sorted((tmp_path / "runs").iterdir())
    assert len(runs) == 2
    second_report = json.loads((runs[1] / "run_report.json").read_text(encoding="utf-8"))
    assert second_report["continued_from"] == runs[0].name
    assert (runs[1] / "workspace" / "app.py").exists()
    output = capsys.readouterr().out
    assert "你好！" in output
    assert "[1/7]" not in output
    assert "已更新项目" in output


def test_greeting_uses_model_but_does_not_start_development(tmp_path):
    class TrackingClient(OfflineClient):
        calls = 0

        def complete_json(self, system, prompt, schema_name):
            self.calls += 1
            return super().complete_json(system, prompt, schema_name)

    client = TrackingClient()
    session = ChatSession(AgentWeaveRuntime(client, tmp_path, verbose=False))
    assert "你好" in session.handle("你好")
    assert client.calls == 1
    assert not (tmp_path / "runs").exists()


def test_model_identity_uses_actual_configuration_after_model_call(tmp_path):
    client = DeepSeekClient.__new__(DeepSeekClient)
    client.model = "deepseek-chat"
    calls = []

    def fake_complete(system, prompt, schema_name):
        calls.append(schema_name)
        return {"intent": "chat", "reply": "我是会话协调器", "requirement": ""}

    client.complete_json = fake_complete
    session = ChatSession(AgentWeaveRuntime(client, tmp_path, verbose=False))
    assert session.handle("你是什么模型") == "当前使用 DeepSeek API，模型是 deepseek-chat。"
    assert calls == ["conversation_turn"]


def test_new_topic_does_not_delete_prior_project(tmp_path):
    session = ChatSession(AgentWeaveRuntime(OfflineClient(), tmp_path, verbose=False))
    session.handle("开发一个问候程序")
    previous = session.last_run
    assert previous is not None
    session.reset()
    assert session.last_run is None
    assert (previous / "workspace" / "app.py").exists()


@pytest.mark.skipif(sys.platform not in {"darwin", "linux"}, reason="POSIX terminal required")
def test_chinese_backspace_mode_is_enabled_and_restored(monkeypatch):
    import pty
    import termios

    master, slave = pty.openpty()
    try:
        initial = termios.tcgetattr(slave)
        initial[0] &= ~0x4000
        termios.tcsetattr(slave, termios.TCSANOW, initial)

        class TerminalInput:
            def fileno(self):
                return slave

            def isatty(self):
                return True

        monkeypatch.setattr(sys, "stdin", TerminalInput())
        with _utf8_terminal_input():
            assert termios.tcgetattr(slave)[0] & 0x4000
        assert not (termios.tcgetattr(slave)[0] & 0x4000)
    finally:
        os.close(master)
        os.close(slave)
