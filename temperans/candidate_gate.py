from dataclasses import dataclass, field, asdict


ATTACH = "attach"
BRANCH = "branch"
NEW = "new"
UNCERTAIN = "uncertain"


@dataclass
class CandidateGateDecision:
    decision: str
    candidate_id: str | None
    confidence: float

    top_score: float | None = None
    second_score: float | None = None
    margin: float | None = None

    reasons: list[str] = field(
        default_factory=list
    )

    def to_dict(self):
        return asdict(self)


class CandidateDecisionGate:
    """
    Multi-candidate safety gate.

    Individual candidate linkers answer:
        "Could this belong to candidate X?"

    This gate answers:
        "Is it safe to choose X over all alternatives?"

    Strong deterministic identity evidence may override
    semantic ranking.

    Otherwise, a weaker candidate must not win when a
    substantially more plausible candidate remains
    unresolved/uncertain.
    """

    def __init__(
        self,
        semantic_override_margin=0.15,
    ):
        self.semantic_override_margin = (
            semantic_override_margin
        )

    def _has_strong_attach(self, decision):
        reasons = getattr(
            decision.evidence,
            "reasons",
            [],
        )

        return any(
            (
                "same strong work identifier"
                in reason.lower()
            )
            for reason in reasons
        )

    def choose(self, decisions):
        """
        decisions:
            list of tuples:
            (
                semantic_score,
                candidate,
                structured_decision,
            )
        """

        if not decisions:
            return CandidateGateDecision(
                decision=NEW,
                candidate_id=None,
                confidence=1.0,
                reasons=[
                    "no candidate trajectories"
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

        margin = (
            top_score - second_score
            if second_score is not None
            else None
        )

        # ------------------------------------------
        # 1. Strong deterministic identity wins.
        # ------------------------------------------

        strong_attaches = [
            item
            for item in ranked
            if (
                item[2].decision == ATTACH
                and self._has_strong_attach(
                    item[2]
                )
            )
        ]

        if strong_attaches:
            strong_attaches.sort(
                key=lambda item: (
                    item[2].confidence,
                    item[0],
                ),
                reverse=True,
            )

            score, candidate, decision = (
                strong_attaches[0]
            )

            return CandidateGateDecision(
                decision=ATTACH,
                candidate_id=(
                    candidate.candidate_id
                ),
                confidence=decision.confidence,
                top_score=top_score,
                second_score=second_score,
                margin=margin,
                reasons=[
                    "strong deterministic trajectory "
                    "anchor overrides semantic ranking"
                ],
            )

        # ------------------------------------------
        # 2. Branch decisions.
        # ------------------------------------------

        branches = [
            item
            for item in ranked
            if item[2].decision == BRANCH
        ]

        if branches:
            branches.sort(
                key=lambda item: (
                    item[2].confidence,
                    item[0],
                ),
                reverse=True,
            )

            score, candidate, decision = (
                branches[0]
            )

            # Don't allow a weak branch candidate to
            # jump over a much stronger unresolved one.
            if (
                score
                < top_score
                - self.semantic_override_margin
            ):
                return CandidateGateDecision(
                    decision=UNCERTAIN,
                    candidate_id=(
                        ranked[0][1].candidate_id
                    ),
                    confidence=0.50,
                    top_score=top_score,
                    second_score=second_score,
                    margin=margin,
                    reasons=[
                        "branch candidate is materially "
                        "weaker than best semantic candidate"
                    ],
                )

            return CandidateGateDecision(
                decision=BRANCH,
                candidate_id=(
                    candidate.candidate_id
                ),
                confidence=decision.confidence,
                top_score=top_score,
                second_score=second_score,
                margin=margin,
                reasons=[
                    "branch decision survives "
                    "multi-candidate safety gate"
                ],
            )

        # ------------------------------------------
        # 3. Non-strong ATTACH.
        # ------------------------------------------

        attaches = [
            item
            for item in ranked
            if item[2].decision == ATTACH
        ]

        if attaches:
            attaches.sort(
                key=lambda item: (
                    item[2].confidence,
                    item[0],
                ),
                reverse=True,
            )

            score, candidate, decision = (
                attaches[0]
            )

            # Critical safety rule:
            #
            # Do not attach to a weaker candidate when
            # a materially stronger semantic candidate
            # remains unresolved.
            if (
                score
                < top_score
                - self.semantic_override_margin
            ):
                return CandidateGateDecision(
                    decision=UNCERTAIN,
                    candidate_id=(
                        ranked[0][1].candidate_id
                    ),
                    confidence=0.50,
                    top_score=top_score,
                    second_score=second_score,
                    margin=margin,
                    reasons=[
                        "local attach candidate is "
                        "materially weaker than best "
                        "semantic candidate",
                        "escalate rather than risk "
                        "wrong-trajectory attachment",
                    ],
                )

            return CandidateGateDecision(
                decision=ATTACH,
                candidate_id=(
                    candidate.candidate_id
                ),
                confidence=decision.confidence,
                top_score=top_score,
                second_score=second_score,
                margin=margin,
                reasons=[
                    "attach candidate remains plausible "
                    "after multi-candidate comparison"
                ],
            )

        # ------------------------------------------
        # 4. NEW only if every candidate says NEW.
        # ------------------------------------------

        if all(
            item[2].decision == NEW
            for item in ranked
        ):
            return CandidateGateDecision(
                decision=NEW,
                candidate_id=None,
                confidence=min(
                    item[2].confidence
                    for item in ranked
                ),
                top_score=top_score,
                second_score=second_score,
                margin=margin,
                reasons=[
                    "all candidate trajectories rejected"
                ],
            )

        # ------------------------------------------
        # 5. Otherwise abstain.
        # ------------------------------------------

        return CandidateGateDecision(
            decision=UNCERTAIN,
            candidate_id=(
                ranked[0][1].candidate_id
            ),
            confidence=0.50,
            top_score=top_score,
            second_score=second_score,
            margin=margin,
            reasons=[
                "candidate set contains unresolved "
                "competing evidence"
            ],
        )
