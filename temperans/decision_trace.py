from dataclasses import dataclass, field, asdict
from typing import Optional
import hashlib
import json


@dataclass
class DecisionRule:
    rule: str
    effect: str
    evidence: dict = field(default_factory=dict)
    explanation: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class DecisionTrace:
    decision: str
    source: str
    confidence: float

    trajectory_id: Optional[str] = None

    candidate_score: Optional[float] = None
    second_score: Optional[float] = None
    margin: Optional[float] = None

    abstained: bool = False
    frontier_used: bool = False

    rules: list[DecisionRule] = field(
        default_factory=list
    )

    input_signature: Optional[str] = None

    def to_dict(self):
        return {
            "decision": self.decision,
            "source": self.source,
            "confidence": self.confidence,
            "trajectory_id": self.trajectory_id,
            "candidate_score": self.candidate_score,
            "second_score": self.second_score,
            "margin": self.margin,
            "abstained": self.abstained,
            "frontier_used": self.frontier_used,
            "rules": [
                rule.to_dict()
                for rule in self.rules
            ],
            "input_signature": self.input_signature,
        }


def deterministic_signature(payload):
    """
    Stable signature for replay/cache/debugging.

    Same normalized payload -> same signature.
    """

    serialized = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )

    return hashlib.sha256(
        serialized.encode("utf-8")
    ).hexdigest()
