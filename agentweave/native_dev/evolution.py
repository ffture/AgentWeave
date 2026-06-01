"""Feedback policy that turns review signals into autonomous evolution."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class EvolutionDecision:
    should_evolve: bool
    score: int
    reasons: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class FeedbackEvolutionPolicy:
    def __init__(self, quality_floor: int = 85) -> None:
        self.quality_floor = quality_floor

    def decide(self, review: Dict[str, Any], verification: Dict[str, Any]) -> EvolutionDecision:
        score = max(0, min(100, int(review.get("score", 0))))
        reasons: List[str] = []
        if not verification.get("passed", False):
            reasons.append("确定性验证未通过")
        if score < self.quality_floor:
            reasons.append(f"质量评分 {score} 低于阈值 {self.quality_floor}")
        opportunities = review.get("refactor_opportunities", [])
        if opportunities:
            reasons.extend(str(item) for item in opportunities)
        return EvolutionDecision(bool(reasons), score, reasons)
