from dataclasses import dataclass, field, asdict


NEW = "new"
UNCERTAIN = "uncertain"


@dataclass
class NoMatchDecision:
    decision: str
    confidence: float

    top_score: float | None = None
    second_score: float | None = None

    reasons: list[str] = field(
        default_factory=list
    )

    def to_dict(self):
        return asdict(self)


class NoMatchGate:
    """
    Conservative global NEW detector.

    This runs only after ordinary local routing
    has abstained.

    V0 supports two deterministic cases:

    1. Retrieval rejection:
       every candidate has extremely weak semantic
       relationship.

    2. Structural rejection:
       the plausible candidate(s) were explicitly
       rejected by deterministic identity evidence.

    It never converts unresolved plausible candidates
    into NEW.
    """

    def __init__(
        self,
        max_no_match_score=0.12,
    ):
        self.max_no_match_score = (
            max_no_match_score
        )

    def choose(
        self,
        *,
        decisions,
    ):
        """
        decisions:
            [
                (
                    semantic_score,
                    candidate,
                    structured_decision,
                )
            ]
        """

        if not decisions:
            return NoMatchDecision(
                decision=NEW,
                confidence=1.0,
                reasons=[
                    "no existing candidate trajectories"
                ],
            )

        ranked = sorted(
            decisions,
            key=lambda item: item[0],
            reverse=True,
        )

        top_score = ranked[0][0]

        second_score = (
            ranked[1][0]
            if len(ranked) > 1
            else None
        )

        # ----------------------------------------
        # 1. Everything is semantically remote.
        # ----------------------------------------

        if top_score < self.max_no_match_score:
            return NoMatchDecision(
                decision=NEW,
                confidence=0.90,
                top_score=top_score,
                second_score=second_score,
                reasons=[
                    "no candidate exceeds conservative "
                    "retrieval plausibility floor"
                ],
            )

        # ----------------------------------------
        # 2. Every plausible candidate is
        # deterministically rejected.
        # ----------------------------------------

        plausible = [
            item
            for item in ranked
            if item[0]
            >= self.max_no_match_score
        ]

        if (
            plausible
            and all(
                item[2].decision == NEW
                for item in plausible
            )
        ):
            return NoMatchDecision(
                decision=NEW,
                confidence=min(
                    item[2].confidence
                    for item in plausible
                ),
                top_score=top_score,
                second_score=second_score,
                reasons=[
                    "all plausible candidate trajectories "
                    "were deterministically rejected"
                ],
            )

        # ----------------------------------------
        # Anything plausible remains unresolved.
        # ----------------------------------------

        return NoMatchDecision(
            decision=UNCERTAIN,
            confidence=0.50,
            top_score=top_score,
            second_score=second_score,
            reasons=[
                "at least one plausible trajectory "
                "remains unresolved"
            ],
        )
