from dataclasses import dataclass, asdict, field

from temperans.workstate import (
    ConversationState,
    TrajectoryState,
)


ATTACH = "attach"
BRANCH = "branch"
NEW = "new"
UNCERTAIN = "uncertain"


@dataclass
class StructuredEvidence:
    shared_entities: list = field(default_factory=list)
    conflicting_entities: list = field(default_factory=list)

    shared_artifacts: list = field(default_factory=list)
    conflicting_artifacts: list = field(default_factory=list)

    reasons: list = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


@dataclass
class StructuredDecision:
    decision: str
    confidence: float
    semantic_score: float
    evidence: StructuredEvidence

    def to_dict(self):
        result = asdict(self)
        result["evidence"] = self.evidence.to_dict()
        return result


class StructuredTrajectoryLinker:
    """
    Temperans Linker V1.

    Identity/state are structured.
    Semantic similarity is supporting evidence only.

    V1 deliberately abstains aggressively.
    """

    def __init__(
        self,
        strong_semantic=0.72,
        plausible_semantic=0.40,
        weak_semantic=0.20,
    ):
        self.strong_semantic = strong_semantic
        self.plausible_semantic = plausible_semantic
        self.weak_semantic = weak_semantic

    def _normalize(self, values):
        return {
            str(value).strip().lower()
            for value in values
            if str(value).strip()
        }

    def _compare_sets(
        self,
        existing,
        incoming,
    ):
        existing = self._normalize(existing)
        incoming = self._normalize(incoming)

        shared = sorted(
            existing & incoming
        )

        # IMPORTANT:
        # Only call this a conflict when BOTH sides provide
        # identity-bearing values and none agree.
        conflicting = []

        if (
            existing
            and incoming
            and not shared
        ):
            conflicting = [
                {
                    "existing": sorted(existing),
                    "incoming": sorted(incoming),
                }
            ]

        return shared, conflicting

    def decide(
        self,
        trajectory: TrajectoryState,
        conversation: ConversationState,
        semantic_score: float,
        branch_signal: bool = False,
        continuation_signal: bool = False,
    ):
        evidence = StructuredEvidence()

        (
            evidence.shared_entities,
            evidence.conflicting_entities,
        ) = self._compare_sets(
            trajectory.entities,
            conversation.entities,
        )

        (
            evidence.shared_artifacts,
            evidence.conflicting_artifacts,
        ) = self._compare_sets(
            trajectory.artifacts,
            conversation.artifacts,
        )

        # ----------------------------------------
        # 1. Structural identity contradiction
        # ----------------------------------------

        if evidence.conflicting_entities:
            evidence.reasons.append(
                "structured entity identity conflicts"
            )

            return StructuredDecision(
                decision=NEW,
                confidence=0.99,
                semantic_score=semantic_score,
                evidence=evidence,
            )

        if evidence.conflicting_artifacts:
            evidence.reasons.append(
                "structured artifact identity conflicts"
            )

            return StructuredDecision(
                decision=NEW,
                confidence=0.99,
                semantic_score=semantic_score,
                evidence=evidence,
            )

        # ----------------------------------------
        # 2. Branch relationship
        # ----------------------------------------

        if branch_signal:
            evidence.reasons.append(
                "new objective derives from existing work"
            )

            return StructuredDecision(
                decision=BRANCH,
                confidence=0.90,
                semantic_score=semantic_score,
                evidence=evidence,
            )

        # ----------------------------------------
        # 3. Exact anchors
        # ----------------------------------------

        if evidence.shared_artifacts:
            evidence.reasons.append(
                "shared artifact provides candidate-scope evidence "
                "but does not prove trajectory identity"
            )

        if evidence.shared_entities:
            evidence.reasons.append(
                "shared entity provides candidate-scope evidence "
                "but does not prove trajectory identity"
            )

        if (
            evidence.shared_artifacts
            or evidence.shared_entities
        ):
            evidence.reasons.append(
                "semantic reasoning required to distinguish "
                "same work from related-but-distinct work"
            )

            return StructuredDecision(
                decision=UNCERTAIN,
                confidence=0.55,
                semantic_score=semantic_score,
                evidence=evidence,
            )

        # ----------------------------------------
        # 4. Explicit continuation + live state
        # ----------------------------------------

        if (
            continuation_signal
            and trajectory.lifecycle
            in {"active", "waiting", "blocked"}
        ):
            evidence.reasons.append(
                "continuation signal against live trajectory"
            )

            return StructuredDecision(
                decision=ATTACH,
                confidence=0.90,
                semantic_score=semantic_score,
                evidence=evidence,
            )

        # ----------------------------------------
        # 5. Resolved trajectory + recurrence
        #
        # Don't guess reopening from similarity alone.
        # Frontier judge should handle this initially.
        # ----------------------------------------

        if trajectory.lifecycle == "resolved":
            evidence.reasons.append(
                "candidate trajectory is resolved; "
                "reopen requires semantic reasoning"
            )

            return StructuredDecision(
                decision=UNCERTAIN,
                confidence=0.50,
                semantic_score=semantic_score,
                evidence=evidence,
            )

        # ----------------------------------------
        # 6. Semantic evidence
        # ----------------------------------------

        if semantic_score >= self.strong_semantic:
            evidence.reasons.append(
                "strong semantic candidate but no "
                "structural identity anchor"
            )

            # Be conservative: similarity alone is not
            # sufficient for silent merge in V1.
            return StructuredDecision(
                decision=UNCERTAIN,
                confidence=0.65,
                semantic_score=semantic_score,
                evidence=evidence,
            )

        if semantic_score < self.weak_semantic:
            evidence.reasons.append(
                "weak semantic relationship"
            )

            # Weak semantic similarity is not sufficient
            # evidence for NEW when the candidate trajectory
            # is still live. Work can evolve substantially
            # in language while preserving the same goal.
            if trajectory.lifecycle in {
                "active",
                "waiting",
                "blocked",
            }:
                evidence.reasons.append(
                    "candidate trajectory is live; "
                    "semantic evolution requires deeper reasoning"
                )

                return StructuredDecision(
                    decision=UNCERTAIN,
                    confidence=0.45,
                    semantic_score=semantic_score,
                    evidence=evidence,
                )

            return StructuredDecision(
                decision=NEW,
                confidence=0.80,
                semantic_score=semantic_score,
                evidence=evidence,
            )

        evidence.reasons.append(
            "insufficient evidence for safe decision"
        )

        return StructuredDecision(
            decision=UNCERTAIN,
            confidence=0.40,
            semantic_score=semantic_score,
            evidence=evidence,
        )
