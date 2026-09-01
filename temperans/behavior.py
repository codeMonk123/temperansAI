from dataclasses import dataclass
from typing import Optional


@dataclass
class BehaviorResult:
    primitive: Optional[str] = None
    confidence: float = 0.0
    history_conditioned: bool = False
    history_match: float | None = None
    model_version: str = "none"

    def to_dict(self):
        return {
            "primitive": self.primitive,
            "confidence": self.confidence,
            "history_conditioned": self.history_conditioned,
            "history_match": self.history_match,
            "model_version": self.model_version,
        }


class BehavioralPerception:
    def perceive(
        self,
        previous_text: str,
        current_text: str,
    ) -> BehaviorResult:
        raise NotImplementedError
