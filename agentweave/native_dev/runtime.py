"""Event-driven runtime for an autonomous software organization."""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from .client import ModelClient
from .domain import RunLedger, Stage
from .evolution import FeedbackEvolutionPolicy
from .knowledge import KnowledgeBase
from .planning import TaskGraph
from .workspace import ArtifactVault, VerificationSuite


class AgentWeaveRuntime:
    """Coordinates cognition while deterministic components enforce invariants."""

    def __init__(
        self,
        client: ModelClient,
        project_root: Path,
        quality_floor: int = 85,
        verbose: bool = True,
    ) -> None:
        self.client = client
        self.project_root = project_root
        self.knowledge = KnowledgeBase(project_root / "knowledge" / "memory.json")
        self.evolution_policy = FeedbackEvolutionPolicy(quality_floor)
        self.verifier = VerificationSuite()
        self.verbose = verbose

    def _ask(self, actor: str, prompt: str, contract: str) -> Dict[str, Any]:
        if self.verbose:
            print(f"  → {actor} 正在工作", flush=True)
        return self.client.complete_json(
            f"你是自治软件组织中的{actor}。你的决定会进入可审计事件日志。",
            prompt,
            contract,
        )

    def _phase(self, position: int, title: str) -> None:
        if self.verbose:
            print(f"[{position}/7] {title}", flush=True)

    def run(self, requirement: str, previous_run: Path | None = None) -> Path:
        started = time.monotonic()
        previous_workspace = None
        if previous_run is not None:
            previous_run = previous_run.resolve()
            if previous_run.parent != (self.project_root / "runs").resolve():
                raise ValueError("只能继续当前输出目录中的上一轮任务")
            previous_workspace = previous_run / "workspace"
            if not previous_workspace.is_dir():
                raise ValueError("上一轮产物不存在，无法继续")
        run_id = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        run_dir = self.project_root / "runs" / run_id
        vault = ArtifactVault(run_dir / "workspace")
        if previous_workspace is not None:
            vault.seed_from(previous_workspace)
        ledger = RunLedger()
        report: Dict[str, Any] = {
            "run_id": run_id,
            "requirement": requirement,
            "runtime": "event-driven-agentweave-v2",
            "artifact_manifest": [],
            "continued_from": previous_run.name if previous_run is not None else None,
        }

        existing_context = vault.snapshot() if previous_run is not None else {}

        self._phase(1, "形成需求契约")
        analysis = self._ask(
            "需求契约智能体",
            "把需求转换为可验证契约。返回 summary、functional_requirements、"
            "quality_requirements、constraints、acceptance_criteria。若有已有项目，"
            "本轮是增量修改，须保留原有能力。\n"
            + json.dumps({"request": requirement, "existing_files": existing_context}, ensure_ascii=False),
            "requirement_analysis",
        )
        report["analysis"] = analysis
        ledger.advance(Stage.ANALYZED, "requirements", "完成需求契约与验收标准")

        self._phase(2, "按能力自组织团队")
        recalled = self.knowledge.recall(requirement)
        team = self._ask(
            "组织拓扑智能体",
            "不要套用固定角色。根据任务风险生成最小充分团队。返回 agents 数组，"
            "每项含 name、role、mission、skills。\n"
            + json.dumps({"contract": analysis, "organizational_memory": recalled}, ensure_ascii=False),
            "team_design",
        )
        report["team"] = team
        ledger.advance(Stage.ORGANIZED, "organization", f"动态形成 {len(team.get('agents', []))} 个角色")

        self._phase(3, "编译任务依赖图")
        plan = self._ask(
            "任务编译智能体",
            "把需求编译为有向无环研发任务图。返回 tasks 数组，每项含 id、title、"
            "agent、description、dependencies；必须覆盖设计、实现和测试。\n"
            + json.dumps({"contract": analysis, "team": team, "existing_files": list(existing_context)}, ensure_ascii=False),
            "task_plan",
        )
        ordered_tasks = TaskGraph(plan.get("tasks", [])).ordered()
        report["plan"] = {**plan, "execution_order": [task["id"] for task in ordered_tasks]}
        ledger.advance(Stage.PLANNED, "planner", f"生成并校验 {len(ordered_tasks)} 个任务")

        self._phase(4, "执行多智能体研发任务")
        completed: List[Dict[str, Any]] = []
        for task in ordered_tasks:
            actor = str(task.get("agent", "自主执行单元"))
            result = self._ask(
                actor,
                "执行当前研发任务。返回 summary、artifacts（path/content 数组）、risks。"
                "文件必须使用相对路径；代码应完整而不是伪代码。已有文件应在原内容基础上修改，"
                "未涉及的文件不要重复输出或删除。\n"
                + json.dumps(
                    {
                        "contract": analysis,
                        "task": task,
                        "available_files": vault.files(),
                        "file_contents": vault.snapshot(),
                        "recent_results": completed[-2:],
                    },
                    ensure_ascii=False,
                ),
                "task_execution",
            )
            changes = vault.apply(result.get("artifacts", []), source=f"task:{task['id']}")
            report["artifact_manifest"].extend(changes)
            completed.append({"task": task, "summary": result.get("summary"), "risks": result.get("risks", [])})
        report["execution"] = completed
        ledger.advance(Stage.BUILT, "delivery", f"执行 {len(completed)} 个任务，当前产物 {len(vault.files())} 个")

        self._phase(5, "执行确定性验证与认知评审")
        verification_before = self.verifier.inspect(vault)
        review = self._ask(
            "质量雷达智能体",
            "结合验收标准和确定性验证主动识别技术债。返回 score（0-100）、strengths、"
            "problems、refactor_opportunities。即使代码能运行，也要检查可维护性和边界条件。\n"
            + json.dumps(
                {"contract": analysis, "verification": verification_before, "files": vault.snapshot()},
                ensure_ascii=False,
            ),
            "quality_review",
        )
        decision = self.evolution_policy.decide(review, verification_before)
        report["verification_before_evolution"] = verification_before
        report["review"] = review
        report["evolution_decision"] = decision.to_dict()
        ledger.advance(Stage.REVIEWED, "quality-radar", f"质量评分 {decision.score}")

        self._phase(6, "应用反馈驱动演化策略")
        if decision.should_evolve:
            if self.verbose:
                print("  ↻ 系统自主创建重构任务", flush=True)
            refactor = self._ask(
                "演化修复智能体",
                "系统已自主决定重构。根据反馈直接修改产物，返回 summary、reason、"
                "artifacts（path/content 数组）。保留正确能力并解决列出的演化原因。\n"
                + json.dumps(
                    {
                        "contract": analysis,
                        "decision": decision.to_dict(),
                        "verification": verification_before,
                        "files": vault.snapshot(),
                    },
                    ensure_ascii=False,
                ),
                "refactor",
            )
            changes = vault.apply(refactor.get("artifacts", []), source="autonomous-evolution")
            report["artifact_manifest"].extend(changes)
            report["evolution"] = refactor
            ledger.advance(Stage.EVOLVED, "evolution-policy", f"完成 {len(changes)} 项自主变更")
        else:
            if self.verbose:
                print("  ✓ 质量门禁通过，无需重构", flush=True)
        report["verification_after_evolution"] = self.verifier.inspect(vault)

        self._phase(7, "提炼组织记忆")
        learning = self._ask(
            "组织学习智能体",
            "从本轮事件、反馈和演化中提炼跨项目可复用知识。返回 lessons 和 tags 数组。\n"
            + json.dumps(
                {
                    "requirement": requirement,
                    "review": review,
                    "decision": decision.to_dict(),
                    "final_verification": report["verification_after_evolution"],
                },
                ensure_ascii=False,
            ),
            "learning",
        )
        learning["requirement"] = requirement
        self.knowledge.add(learning)
        report["learning"] = learning
        ledger.advance(Stage.LEARNED, "organizational-memory", "沉淀本轮可复用经验")
        ledger.advance(Stage.COMPLETED, "runtime", "研发闭环完成")

        report["timeline"] = ledger.to_list()
        report["metrics"] = {
            "duration_seconds": round(time.monotonic() - started, 3),
            "agents": len(team.get("agents", [])),
            "tasks": len(ordered_tasks),
            "files": len(vault.files()),
            "artifact_revisions": len(report["artifact_manifest"]),
        }
        (run_dir / "run_report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        if self.verbose:
            print(f"完成：{run_dir}", flush=True)
        return run_dir
