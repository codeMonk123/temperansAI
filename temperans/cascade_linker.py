from dataclasses import dataclass, asdict


ATTACH = "attach"
BRANCH = "branch"
NEW = "new"
CLARIFY = "clarify"


@dataclass
class CascadeDecision:
    decision: str
    confidence: float
    source: str
    reasons: list
    frontier_used: bool = False
    frontier_available: bool = True

    def to_dict(self):
        return asdict(self)


class CascadeTrajectoryLinker:
    """
    Production-oriented Temperans routing cascade.

    1. Structured/local linker handles safe cases.
    2. Frontier semantic judge handles ambiguous cases.
    3. If frontier remains uncertain or unavailable,
       Temperans asks the user instead of guessing.
    """

    def __init__(
        self,
        structured_linker,
        frontier_judge=None,
        frontier_confidence_threshold=0.80,
    ):
        self.structured_linker = structured_linker
        self.frontier_judge = frontier_judge
        self.frontier_confidence_threshold = (
            frontier_confidence_threshold
        )

    def decide(
        self,
        trajectory,
        conversation,
        semantic_score,
        branch_signal=False,
        continuation_signal=False,
    ):
        local = self.structured_linker.decide(
            trajectory=trajectory,
            conversation=conversation,
            semantic_score=semantic_score,
            branch_signal=branch_signal,
            continuation_signal=continuation_signal,
        )

        # Local Temperans made a safe decision.
        if local.decision != "uncertain":
            return CascadeDecision(
                decision=local.decision,
                confidence=local.confidence,
                source="temperans_local",
                reasons=list(
                    local.evidence.reasons
                ),
                frontier_used=False,
            )

        # No frontier provider configured.
        if self.frontier_judge is None:
            return CascadeDecision(
                decision=CLARIFY,
                confidence=local.confidence,
                source="user_clarification",
                reasons=[
                    "local trajectory evidence is ambiguous",
                    "no frontier semantic judge configured",
                ],
                frontier_used=False,
                frontier_available=False,
            )

        # Escalate only ambiguous cases.
        try:
            frontier = self.frontier_judge.judge(
                trajectory=trajectory,
                conversation=conversation,
                structural_evidence=(
                    local.evidence.to_dict()
                ),
            )

        except Exception as exc:
            return CascadeDecision(
                decision=CLARIFY,
                confidence=local.confidence,
                source="user_clarification",
                reasons=[
                    "local trajectory evidence is ambiguous",
                    "frontier semantic judge unavailable",
                    type(exc).__name__,
                ],
                frontier_used=True,
                frontier_available=False,
            )

        if (
            frontier.decision
            in {ATTACH, BRANCH, NEW}
            and frontier.confidence
            >= self.frontier_confidence_threshold
        ):
            return CascadeDecision(
                decision=frontier.decision,
                confidence=frontier.confidence,
                source="frontier_judge",
                reasons=list(frontier.reasons),
                frontier_used=True,
                frontier_available=True,
            )

        return CascadeDecision(
            decision=CLARIFY,
            confidence=frontier.confidence,
            source="user_clarification",
            reasons=[
                "frontier judgment remained ambiguous",
                *frontier.reasons,
            ],
            frontier_used=True,
            frontier_available=True,
        )
