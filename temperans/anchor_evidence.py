from dataclasses import dataclass, field, asdict

from temperans.anchors import (
    Anchor,
    AnchorStrength,
)


@dataclass
class RuleTrace:
    rule: str
    anchor_type: str
    strength: str
    existing: list = field(default_factory=list)
    incoming: list = field(default_factory=list)
    effect: str = ""
    explanation: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class AnchorEvidence:
    hard_new: bool = False
    strong_attach: bool = False

    boundary_matches: list = field(default_factory=list)
    boundary_mismatches: list = field(default_factory=list)

    strong_matches: list = field(default_factory=list)
    medium_matches: list = field(default_factory=list)
    scope_matches: list = field(default_factory=list)

    traces: list[RuleTrace] = field(default_factory=list)

    def to_dict(self):
        return {
            "hard_new": self.hard_new,
            "strong_attach": self.strong_attach,
            "boundary_matches": self.boundary_matches,
            "boundary_mismatches": self.boundary_mismatches,
            "strong_matches": self.strong_matches,
            "medium_matches": self.medium_matches,
            "scope_matches": self.scope_matches,
            "traces": [
                trace.to_dict()
                for trace in self.traces
            ],
        }


class AnchorEvidenceEngine:
    """
    Deterministic comparison of typed anchors.

    Important semantics:

    BOUNDARY
      Different explicit values -> hard NEW evidence.

    STRONG
      Same exact value -> strong ATTACH evidence.

    MEDIUM
      Same exact value -> supporting evidence only.

    SCOPE
      Same exact value -> candidate retrieval evidence only.
    """

    def _group(self, anchors):
        grouped = {}

        for anchor in anchors:
            grouped.setdefault(
                anchor.type,
                [],
            ).append(anchor)

        return grouped

    def _values(self, anchors):
        return {
            anchor.value.strip().lower()
            for anchor in anchors
        }

    def compare(
        self,
        existing: list[Anchor],
        incoming: list[Anchor],
    ) -> AnchorEvidence:
        result = AnchorEvidence()

        left = self._group(existing)
        right = self._group(incoming)

        common_types = sorted(
            set(left) & set(right)
        )

        for anchor_type in common_types:
            left_anchors = left[anchor_type]
            right_anchors = right[anchor_type]

            left_values = self._values(
                left_anchors
            )

            right_values = self._values(
                right_anchors
            )

            shared = sorted(
                left_values & right_values
            )

            strength = (
                left_anchors[0].strength
            )

            # ---------------------------------
            # BOUNDARY
            # ---------------------------------

            if strength == AnchorStrength.BOUNDARY:
                if shared:
                    result.boundary_matches.extend(
                        [
                            f"{anchor_type}:{value}"
                            for value in shared
                        ]
                    )

                    result.traces.append(
                        RuleTrace(
                            rule="boundary_match",
                            anchor_type=anchor_type,
                            strength=strength.value,
                            existing=sorted(left_values),
                            incoming=sorted(right_values),
                            effect="support",
                            explanation=(
                                "same explicit identity boundary"
                            ),
                        )
                    )

                elif left_values and right_values:
                    result.hard_new = True

                    result.boundary_mismatches.append({
                        "type": anchor_type,
                        "existing": sorted(left_values),
                        "incoming": sorted(right_values),
                    })

                    result.traces.append(
                        RuleTrace(
                            rule="boundary_mismatch",
                            anchor_type=anchor_type,
                            strength=strength.value,
                            existing=sorted(left_values),
                            incoming=sorted(right_values),
                            effect="new",
                            explanation=(
                                "different explicit identity "
                                "boundaries must not be merged"
                            ),
                        )
                    )

                continue

            # No exact match -> nothing deterministic
            # for STRONG/MEDIUM/SCOPE in V0.
            if not shared:
                continue

            # ---------------------------------
            # STRONG
            # ---------------------------------

            if strength == AnchorStrength.STRONG:
                result.strong_attach = True

                result.strong_matches.extend(
                    [
                        f"{anchor_type}:{value}"
                        for value in shared
                    ]
                )

                result.traces.append(
                    RuleTrace(
                        rule="strong_anchor_match",
                        anchor_type=anchor_type,
                        strength=strength.value,
                        existing=sorted(left_values),
                        incoming=sorted(right_values),
                        effect="attach",
                        explanation=(
                            "same strong work identifier"
                        ),
                    )
                )

            # ---------------------------------
            # MEDIUM
            # ---------------------------------

            elif strength == AnchorStrength.MEDIUM:
                result.medium_matches.extend(
                    [
                        f"{anchor_type}:{value}"
                        for value in shared
                    ]
                )

                result.traces.append(
                    RuleTrace(
                        rule="medium_anchor_match",
                        anchor_type=anchor_type,
                        strength=strength.value,
                        existing=sorted(left_values),
                        incoming=sorted(right_values),
                        effect="support",
                        explanation=(
                            "supporting work-context evidence"
                        ),
                    )
                )

            # ---------------------------------
            # SCOPE
            # ---------------------------------

            elif strength == AnchorStrength.SCOPE:
                result.scope_matches.extend(
                    [
                        f"{anchor_type}:{value}"
                        for value in shared
                    ]
                )

                result.traces.append(
                    RuleTrace(
                        rule="scope_anchor_match",
                        anchor_type=anchor_type,
                        strength=strength.value,
                        existing=sorted(left_values),
                        incoming=sorted(right_values),
                        effect="candidate_only",
                        explanation=(
                            "same scope helps retrieval but "
                            "does not prove trajectory identity"
                        ),
                    )
                )

        # Boundary mismatch always dominates.
        if result.hard_new:
            result.strong_attach = False

        return result
