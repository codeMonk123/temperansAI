from dataclasses import dataclass, field, asdict


ATTACH = "attach"
BRANCH = "branch"
NEW = "new"
UNCERTAIN = "uncertain"
CLARIFY = "clarify"


@dataclass
class CandidateSetDecision:
    decision: str
    candidate_id: str | None
    confidence: float
    reasons: list[str] = field(default_factory=list)

    rejected_candidates: list[str] = field(
        default_factory=list
    )

    unresolved_candidates: list[str] = field(
        default_factory=list
    )

    def to_dict(self):
        return asdict(self)


class CandidateSetResolver:
    """
    Deterministic reasoning over the entire candidate set.

    This component does NOT decide whether an individual
    candidate matches. The StructuredTrajectoryLinker
    already does that.

    It answers:
        What does the complete set of candidate decisions imply?
    """

    def resolve(self, decisions):
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
            return CandidateSetDecision(
                decision=NEW,
                candidate_id=None,
                confidence=1.0,
                reasons=[
                    "no existing candidate trajectories"
                ],
            )

        attaches = []
        branches = []
        rejected = []
        unresolved = []

        for score, candidate, decision in decisions:
            candidate_id = candidate.candidate_id

            if decision.decision == ATTACH:
                attaches.append(
                    (
                        score,
                        candidate,
                        decision,
                    )
                )

            elif decision.decision == BRANCH:
                branches.append(
                    (
                        score,
                        candidate,
                        decision,
                    )
                )

            elif decision.decision == NEW:
                rejected.append(candidate_id)

            else:
                unresolved.append(candidate_id)

        # -----------------------------------------
        # Positive candidates still require the
        # CandidateDecisionGate.
        # -----------------------------------------

        if attaches or branches:
            return CandidateSetDecision(
                decision=UNCERTAIN,
                candidate_id=None,
                confidence=0.50,
                reasons=[
                    "positive candidate exists; "
                    "multi-candidate safety gate required"
                ],
                rejected_candidates=rejected,
                unresolved_candidates=unresolved,
            )

        # -----------------------------------------
        # Every candidate definitively rejected.
        # -----------------------------------------

        if (
            len(rejected) == len(decisions)
            and not unresolved
        ):
            confidence = min(
                decision.confidence
                for _, _, decision in decisions
            )

            return CandidateSetDecision(
                decision=NEW,
                candidate_id=None,
                confidence=confidence,
                reasons=[
                    "all existing trajectories were "
                    "deterministically rejected"
                ],
                rejected_candidates=rejected,
                unresolved_candidates=[],
            )

        # -----------------------------------------
        # Some rejected, some unresolved.
        #
        # Never turn unresolved evidence into NEW.
        # -----------------------------------------

        return CandidateSetDecision(
            decision=UNCERTAIN,
            candidate_id=(
                unresolved[0]
                if len(unresolved) == 1
                else None
            ),
            confidence=0.50,
            reasons=[
                "at least one candidate remains unresolved"
            ],
            rejected_candidates=rejected,
            unresolved_candidates=unresolved,
        )
