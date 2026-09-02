from dataclasses import dataclass, asdict

from temperans.linkage import LinkageEvidenceExtractor


ATTACH = "attach"
BRANCH = "branch"
NEW = "new"
UNCERTAIN = "uncertain"


@dataclass
class LinkageDecision:
    decision: str
    confidence: float
    semantic_score: float
    evidence: dict
    reasons: list

    def to_dict(self):
        return asdict(self)


class HybridTrajectoryLinker:
    """
    First Temperans-specific trajectory linker.

    Semantic similarity is evidence, not identity.

    Hard contradictions can veto a semantic match.
    Branch evidence can preserve relationship without merging.
    Continuation evidence can rescue semantically weak matches.

    Ambiguous cases abstain rather than forcing a merge.
    """

    def __init__(
        self,
        evidence_extractor=None,
        strong_semantic_attach=0.72,
        plausible_semantic_attach=0.40,
        low_semantic=0.20,
    ):
        self.evidence_extractor = (
            evidence_extractor
            or LinkageEvidenceExtractor()
        )

        self.strong_semantic_attach = (
            strong_semantic_attach
        )

        self.plausible_semantic_attach = (
            plausible_semantic_attach
        )

        self.low_semantic = low_semantic

    def decide(
        self,
        candidate_text,
        new_text,
        semantic_score,
        trajectory_unresolved=False,
    ):
        evidence = self.evidence_extractor.extract(
            candidate_text=candidate_text,
            new_text=new_text,
        )

        reasons = []

        # ------------------------------------------
        # 1. Identity contradiction veto
        # ------------------------------------------

        if evidence.has_contradiction:
            reasons.extend(
                evidence.contradictions
            )

            reasons.append(
                "identity contradiction overrides "
                "semantic similarity"
            )

            return LinkageDecision(
                decision=NEW,
                confidence=0.99,
                semantic_score=semantic_score,
                evidence=evidence.to_dict(),
                reasons=reasons,
            )

        # ------------------------------------------
        # 2. Explicit branch relationship
        # ------------------------------------------

        if evidence.has_branch_signal:
            reasons.extend(
                evidence.branch_signals
            )

            reasons.append(
                "related work appears to start "
                "a distinct objective"
            )

            return LinkageDecision(
                decision=BRANCH,
                confidence=0.90,
                semantic_score=semantic_score,
                evidence=evidence.to_dict(),
                reasons=reasons,
            )

        # ------------------------------------------
        # 3. Contextual continuation
        # ------------------------------------------

        if evidence.has_continuation_signal:
            reasons.extend(
                evidence.continuation_signals
            )

            if trajectory_unresolved:
                reasons.append(
                    "candidate trajectory remains unresolved"
                )

                reasons.append(
                    "continuation evidence rescues "
                    "weak lexical/semantic similarity"
                )

                return LinkageDecision(
                    decision=ATTACH,
                    confidence=0.90,
                    semantic_score=semantic_score,
                    evidence=evidence.to_dict(),
                    reasons=reasons,
                )

            reasons.append(
                "continuation language exists but "
                "trajectory state is insufficient"
            )

            return LinkageDecision(
                decision=UNCERTAIN,
                confidence=0.55,
                semantic_score=semantic_score,
                evidence=evidence.to_dict(),
                reasons=reasons,
            )

        # ------------------------------------------
        # 4. Strong semantic match
        #
        # Still not enough for extreme-confidence
        # production auto-attach, but useful V0.
        # ------------------------------------------

        if semantic_score >= self.strong_semantic_attach:
            reasons.append(
                "strong semantic relationship"
            )

            return LinkageDecision(
                decision=ATTACH,
                confidence=0.80,
                semantic_score=semantic_score,
                evidence=evidence.to_dict(),
                reasons=reasons,
            )

        # ------------------------------------------
        # 5. Plausible semantic candidate
        #
        # Don't guess. Escalate later.
        # ------------------------------------------

        if semantic_score >= self.plausible_semantic_attach:
            reasons.append(
                "plausible semantic relationship "
                "without enough identity evidence"
            )

            return LinkageDecision(
                decision=UNCERTAIN,
                confidence=0.50,
                semantic_score=semantic_score,
                evidence=evidence.to_dict(),
                reasons=reasons,
            )

        # ------------------------------------------
        # 6. Very weak relationship
        # ------------------------------------------

        if semantic_score < self.low_semantic:
            reasons.append(
                "weak semantic relationship"
            )

            return LinkageDecision(
                decision=NEW,
                confidence=0.80,
                semantic_score=semantic_score,
                evidence=evidence.to_dict(),
                reasons=reasons,
            )

        # ------------------------------------------
        # 7. Everything else abstains
        # ------------------------------------------

        reasons.append(
            "insufficient evidence for safe routing"
        )

        return LinkageDecision(
            decision=UNCERTAIN,
            confidence=0.40,
            semantic_score=semantic_score,
            evidence=evidence.to_dict(),
            reasons=reasons,
        )
