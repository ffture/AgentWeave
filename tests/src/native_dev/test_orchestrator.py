import json
from pathlib import Path

from agentweave.native_dev.client import OfflineClient
from agentweave.native_dev.client import _extract_json
from agentweave.native_dev.domain import RunLedger, Stage
from agentweave.native_dev.evolution import FeedbackEvolutionPolicy
from agentweave.native_dev.knowledge import KnowledgeBase
from agentweave.native_dev.planning import TaskGraph
from agentweave.native_dev.runtime import AgentWeaveRuntime
from agentweave.native_dev.workspace import ArtifactVault


def test_offline_full_lifecycle(tmp_path: Path):
    run_dir = AgentWeaveRuntime(OfflineClient(), tmp_path).run("开发一个问候程序")
    report = json.loads((run_dir / "run_report.json").read_text(encoding="utf-8"))

    assert report["team"]["agents"]
    assert report["evolution"]["reason"]
    assert report["verification_after_evolution"]["passed"] is True
    assert report["timeline"][-1]["stage"] == "completed"
    assert report["artifact_manifest"]
    assert all(set(change) == {"path", "source"} for change in report["artifact_manifest"])
    assert (run_dir / "workspace" / "app.py").exists()
    assert (tmp_path / "knowledge" / "memory.json").exists()


def test_revision_inherits_untouched_files(tmp_path: Path):
    runtime = AgentWeaveRuntime(OfflineClient(), tmp_path, verbose=False)
    first = runtime.run("开发一个问候程序")
    (first / "workspace" / "notes.txt").write_text("keep this", encoding="utf-8")

    second = runtime.run("给刚才的项目增加功能", previous_run=first)

    assert (second / "workspace" / "notes.txt").read_text(encoding="utf-8") == "keep this"
    report = json.loads((second / "run_report.json").read_text(encoding="utf-8"))
    assert report["continued_from"] == first.name


def test_knowledge_recall(tmp_path: Path):
    knowledge = KnowledgeBase(tmp_path / "memory.json")
    knowledge.add({"lessons": ["测试需要覆盖边界"], "tags": ["testing"]})

    assert knowledge.recall("如何做好 testing")


def test_rejects_path_escape(tmp_path: Path):
    try:
        ArtifactVault(tmp_path).resolve("../escape.py")
        assert False, "expected unsafe path to be rejected"
    except ValueError:
        pass


def test_task_graph_is_topologically_scheduled():
    tasks = [
        {"id": "test", "dependencies": ["code"]},
        {"id": "design", "dependencies": []},
        {"id": "code", "dependencies": ["design"]},
    ]

    ordered = TaskGraph(tasks).ordered()

    assert [task["id"] for task in ordered] == ["design", "code", "test"]


def test_json_extraction_accepts_fenced_response():
    assert _extract_json('```json\n{"status": "ok"}\n```') == {"status": "ok"}


def test_evolution_policy_combines_model_and_verifier_signals():
    decision = FeedbackEvolutionPolicy(85).decide(
        {"score": 90, "refactor_opportunities": ["拆分过长函数"]},
        {"passed": True},
    )

    assert decision.should_evolve is True
    assert "拆分过长函数" in decision.reasons


def test_lifecycle_ledger_rejects_invalid_transition():
    ledger = RunLedger()
    try:
        ledger.advance(Stage.BUILT, "test", "跳过前序阶段")
        assert False, "expected invalid transition to be rejected"
    except ValueError:
        pass
