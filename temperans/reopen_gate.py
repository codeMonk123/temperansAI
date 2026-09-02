from dataclasses import dataclass, field, asdict

from temperans.lifecycle import LifecycleEvidenceEngine


ATTACH = "attach"
UNCERTAIN = "uncertain"


@dataclass
class ReopenDecision:
    decision: str
    candidate_id: str | None
    confidence: float
    top_score: float | None = None
    second_score: float | None = None
    margin: float | None = None
    reasons: list[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


class ReopenGate:
    """
    Conservative deterministic gate for resolved trajectories.

    Reopen language alone is NOT enough.

    V0 requires:
      1. semantic top-1 candidate is resolved
      2. explicit recurrence language exists
      3. top-1 has sufficient separation from top-2

    Otherwise abstain.
    """

    def __init__(
        self,
        min_score=0.25,
        min_margin=0.15,
    ):
        self.min_score = min_score
        self.min_margin = min_margin
        self.lifecycle = LifecycleEvidenceEngine()

    def choose(
        self,
        *,
        ranked_candidates,
        incoming_text,
    ):
        """
        ranked_candidates:
            [(semantic_score, candidate), ...]

        candidate must expose:
            candidate_id
            lifecycle
        """

        if not ranked_candidates:
            return ReopenDecision(
                decision=UNCERTAIN,
                candidate_id=None,
                confidence=0.0,
                reasons=["no candidates"],
            )

        ranked = sorted(
            ranked_candidates,
            key=lambda item: item[0],
            reverse=True,
        )

        top_score, top = ranked[0]

        second_score = (
            ranked[1][0]
            if len(ranked) > 1
            else None
        )

        margin = (
            top_score - second_score
            if second_score is not None
            else top_score
        )

        evidence = self.lifecycle.extract(
            lifecycle=top.lifecycle,
            incoming_text=incoming_text,
        )

        if not evidence.reopen_signal:
            return ReopenDecision(
                decision=UNCERTAIN,
                candidate_id=top.candidate_id,
                confidence=0.50,
                top_score=top_score,
                second_score=second_score,
                margin=margin,
                reasons=[
                    "semantic top candidate lacks "
                    "resolved recurrence evidence"
                ],
            )

        if top_score < self.min_score:
            return ReopenDecision(
                decision=UNCERTAIN,
                candidate_id=top.candidate_id,
                confidence=0.50,
                top_score=top_score,
                second_score=second_score,
                margin=margin,
                reasons=[
                    "reopen language exists but candidate "
                    "semantic score is too weak"
                ],
            )

        if margin < self.min_margin:
            return ReopenDecision(
                decision=UNCERTAIN,
                candidate_id=top.candidate_id,
                confidence=0.50,
                top_score=top_score,
                second_score=second_score,
                margin=margin,
                reasons=[
                    "reopen language exists but multiple "
                    "candidates remain plausible"
                ],
            )

        return ReopenDecision(
            decision=ATTACH,
            candidate_id=top.candidate_id,
            confidence=0.92,
            top_score=top_score,
            second_score=second_score,
            margin=margin,
            reasons=[
                "semantic top candidate is resolved",
                "explicit recurrence language detected",
                "candidate separation is sufficient",
            ],
        )
