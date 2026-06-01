"""Command-line interface for the AI-native development team."""

from __future__ import annotations

import argparse
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .chat import ChatSession
from .client import DeepSeekClient, OfflineClient
from .knowledge import KnowledgeBase
from .runtime import AgentWeaveRuntime


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AgentWeave：自组织、自进化的软件开发智能体团队")
    parser.add_argument("requirement", nargs="?", help="用自然语言描述要开发的软件")
    parser.add_argument("--chat", action="store_true", help="进入可连续对话和迭代项目的交互模式")
    parser.add_argument("--offline", action="store_true", help="使用确定性离线模型演示完整流程")
    parser.add_argument("--learn", metavar="FILE_OR_URL", help="学习一个本地文本文件或网页")
    parser.add_argument("--output", default=".", help="运行记录、产物和知识库的保存目录")
    return parser


@contextmanager
def _utf8_terminal_input() -> Iterator[None]:
    """Make canonical-mode Backspace erase whole Chinese characters on macOS/Linux."""
    if sys.platform not in {"darwin", "linux"} or not sys.stdin.isatty():
        yield
        return
    try:
        import termios

        fd = sys.stdin.fileno()
        original = termios.tcgetattr(fd)
        # macOS exposes the flag through stty but not through Python's termios.
        iutf8 = getattr(termios, "IUTF8", 0x4000)
        changed = not bool(original[0] & iutf8)
        if changed:
            updated = original.copy()
            updated[0] |= iutf8
            termios.tcsetattr(fd, termios.TCSANOW, updated)
    except (OSError, ValueError, ImportError):
        yield
        return
    try:
        yield
    finally:
        if changed:
            try:
                current = termios.tcgetattr(fd)
                current[0] = (current[0] & ~iutf8) | (original[0] & iutf8)
                termios.tcsetattr(fd, termios.TCSANOW, current)
            except OSError:
                pass


def interactive_loop(runtime: AgentWeaveRuntime, first_requirement: str | None = None) -> int:
    with _utf8_terminal_input():
        return _run_interactive_loop(runtime, first_requirement)


def _run_interactive_loop(runtime: AgentWeaveRuntime, first_requirement: str | None = None) -> int:
    runtime.verbose = False
    session = ChatSession(runtime)
    print("AgentWeave 已就绪。直接聊天或描述开发需求；/help 查看命令。")
    pending = first_requirement
    while True:
        try:
            message = pending if pending is not None else input("你> ")
        except (EOFError, KeyboardInterrupt):
            print("\n已退出交互模式。")
            return 0
        pending = None
        message = message.strip()
        if not message:
            continue
        if message in {"/exit", "/quit"}:
            print("已退出交互模式。")
            return 0
        if message == "/help":
            print("聊天、描述开发需求、继续修改刚才的项目；/status 查看产物，/new 开始新话题，/exit 退出。")
            continue
        if message == "/new":
            print(f"助手> {session.reset()}")
            continue
        if message == "/status":
            print(f"助手> {session.status()}")
            continue
        try:
            print(f"助手> {session.handle(message)}")
        except KeyboardInterrupt:
            print("\n本次任务已中断，可以继续输入。")
        except (RuntimeError, ValueError, OSError) as exc:
            print(f"助手> 本次处理失败：{exc}")


def main() -> int:
    args = build_parser().parse_args()
    client = OfflineClient() if args.offline else DeepSeekClient()
    root = Path(args.output).resolve()
    if args.learn:
        result = KnowledgeBase(root / "knowledge" / "memory.json").learn_external(args.learn, client)
        print(f"已学习：{result.get('title', args.learn)}")
        return 0
    runtime = AgentWeaveRuntime(client, root)
    if args.chat:
        return interactive_loop(runtime, args.requirement)
    if not args.requirement:
        raise SystemExit("请提供软件需求，或使用 --chat 进入交互模式")
    try:
        runtime.run(args.requirement)
    except RuntimeError as exc:
        print(f"运行失败：{exc}")
        return 1
    return 0
