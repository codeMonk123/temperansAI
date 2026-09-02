import json
from collections import defaultdict

from temperans.anchors import AnchorExtractor
from temperans.linkage import LinkageEvidenceExtractor
from temperans.structured_linker import (
    StructuredTrajectoryLinker,
    UNCERTAIN,
)
from temperans.candidate_gate import (
    CandidateDecisionGate,
)
from temperans.candidate_set import (
    CandidateSetResolver,
)
from temperans.reopen_gate import (
    ReopenGate,
)
from temperans.no_match_gate import (
    NoMatchGate,
)
from temperans.ttlb_v2 import build_v2
from temperans.workstate import (
    ConversationState,
    TrajectoryState,
)


def candidate_text(candidate):
    return " ".join(
        x for x in [
            candidate.goal,
            candidate.state,
            candidate.text,
        ]
        if x
    )


def main():
    cases = build_v2()

    with open(
        "ttlb_v2_semantic_scores.json",
        "r",
        encoding="utf-8",
    ) as f:
        score_rows = json.load(f)

    scores = {
        (
            row["case_id"],
            row["candidate_id"],
        ): float(row["semantic_score"])
        for row in score_rows
    }

    extractor = AnchorExtractor()
    language = LinkageEvidenceExtractor()
    linker = StructuredTrajectoryLinker()
    candidate_gate = CandidateDecisionGate()
    candidate_set = CandidateSetResolver()
    reopen_gate = ReopenGate(
        min_score=0.25,
        min_margin=0.15,
    )

    no_match_gate = NoMatchGate(
        max_no_match_score=0.12,
    )

    metrics = {
        "total": len(cases),
        "auto_decided": 0,
        "correct": 0,
        "abstained": 0,
        "false_merges": 0,
        "false_splits": 0,
        "correct_candidate": 0,
    }

    by_category = defaultdict(
        lambda: {
            "total": 0,
            "decided": 0,
            "correct": 0,
            "abstained": 0,
            "false_merges": 0,
        }
    )

    failures = []

    margins = []

    for case in cases:
        ranked = sorted(
            [
                (
                    scores[
                        (
                            case.case_id,
                            candidate.candidate_id,
                        )
                    ],
                    candidate,
                )
                for candidate in case.candidates
            ],
            key=lambda x: x[0],
            reverse=True,
        )

        top_score = ranked[0][0]
        second_score = ranked[1][0]

        margin = top_score - second_score
        margins.append(margin)

        decisions = []

        for score, candidate in ranked:
            old_text = candidate_text(
                candidate
            )

            trajectory = TrajectoryState(
                trajectory_id=(
                    candidate.candidate_id
                ),
                workspace_id="ttlb_v2",
                person_id="benchmark_user",
                durable_goal=candidate.goal,
                current_state=candidate.state,
                lifecycle=candidate.lifecycle,
                anchors=extractor.extract(
                    old_text
                ),
            )

            conversation = ConversationState(
                workspace_id="ttlb_v2",
                person_id="benchmark_user",
                conversation_id=(
                    "incoming_" + case.case_id
                ),
                surface="benchmark",
                current_problem=(
                    case.incoming_text
                ),
                anchors=extractor.extract(
                    case.incoming_text
                ),
            )

            lang = language.extract(
                candidate_text=old_text,
                new_text=case.incoming_text,
            )

            decision = linker.decide(
                trajectory=trajectory,
                conversation=conversation,
                semantic_score=score,
                branch_signal=(
                    lang.has_branch_signal
                ),
                continuation_signal=(
                    lang.has_continuation_signal
                ),
            )

            decisions.append(
                (
                    score,
                    candidate,
                    decision,
                )
            )

        # ----------------------------------------
        # Multi-candidate safety gate.
        # ----------------------------------------

        # First reason about the candidate set as a whole.
        set_result = candidate_set.resolve(
            decisions
        )

        chosen_candidate = None

        if set_result.decision == "new":
            local_decision = "new"

        elif set_result.decision == "uncertain":
            # Positive candidates still require the
            # multi-candidate safety gate.
            has_positive = any(
                decision.decision
                in {"attach", "branch"}
                for _, _, decision in decisions
            )

            if has_positive:
                gate_result = candidate_gate.choose(
                    decisions
                )

                local_decision = (
                    gate_result.decision
                )

                if (
                    gate_result.candidate_id
                    is not None
                ):
                    chosen_candidate = next(
                        (
                            candidate
                            for candidate
                            in case.candidates
                            if candidate.candidate_id
                            == gate_result.candidate_id
                        ),
                        None,
                    )

            else:
                local_decision = "uncertain"

                if (
                    set_result.candidate_id
                    is not None
                ):
                    chosen_candidate = next(
                        (
                            candidate
                            for candidate
                            in case.candidates
                            if candidate.candidate_id
                            == set_result.candidate_id
                        ),
                        None,
                    )

        else:
            local_decision = (
                set_result.decision
            )

        # ----------------------------------------
        # Conservative lifecycle/reopen recovery.
        #
        # Only runs when normal local routing abstains.
        # It never overrides an existing local decision.
        # ----------------------------------------

        if local_decision == UNCERTAIN:
            reopen_result = reopen_gate.choose(
                ranked_candidates=[
                    (
                        score,
                        candidate,
                    )
                    for score, candidate in ranked
                ],
                incoming_text=case.incoming_text,
            )

            if reopen_result.decision == "attach":
                local_decision = "attach"

                chosen_candidate = next(
                    (
                        candidate
                        for candidate in case.candidates
                        if candidate.candidate_id
                        == reopen_result.candidate_id
                    ),
                    None,
                )

        # ----------------------------------------
        # Conservative global NEW recovery.
        #
        # Runs only if:
        #   normal routing abstained
        #   AND reopen recovery abstained.
        #
        # It may return NEW when:
        #   - no candidate is remotely plausible, or
        #   - every plausible candidate was
        #     deterministically rejected.
        # ----------------------------------------

        if local_decision == UNCERTAIN:
            no_match_result = no_match_gate.choose(
                decisions=decisions
            )

            if no_match_result.decision == "new":
                local_decision = "new"
                chosen_candidate = None

        category = by_category[
            case.category
        ]

        category["total"] += 1

        if local_decision == UNCERTAIN:
            metrics["abstained"] += 1
            category["abstained"] += 1
            continue

        metrics["auto_decided"] += 1
        category["decided"] += 1

        correct = (
            local_decision
            == case.expected_decision
        )

        if (
            correct
            and case.expected_candidate_id
            is not None
        ):
            correct = (
                chosen_candidate is not None
                and chosen_candidate.candidate_id
                == case.expected_candidate_id
            )

        if correct:
            metrics["correct"] += 1
            category["correct"] += 1

            if (
                case.expected_candidate_id
                is not None
            ):
                metrics[
                    "correct_candidate"
                ] += 1

        else:
            if (
                local_decision == "attach"
                and (
                    case.expected_decision != "attach"
                    or (
                        case.expected_candidate_id is not None
                        and (
                            chosen_candidate is None
                            or chosen_candidate.candidate_id
                            != case.expected_candidate_id
                        )
                    )
                )
            ):
                metrics["false_merges"] += 1
                category["false_merges"] += 1

            if (
                local_decision == "new"
                and case.expected_decision
                == "attach"
            ):
                metrics["false_splits"] += 1

            failures.append({
                "case_id": case.case_id,
                "category": case.category,
                "expected": (
                    case.expected_decision
                ),
                "expected_candidate": (
                    case.expected_candidate_id
                ),
                "decision": local_decision,
                "chosen_candidate": (
                    chosen_candidate.candidate_id
                    if chosen_candidate
                    else None
                ),
                "top_score": top_score,
                "second_score": second_score,
                "margin": margin,
            })

    decided = metrics["auto_decided"]

    coverage = (
        decided / metrics["total"]
        if metrics["total"]
        else 0.0
    )

    precision = (
        metrics["correct"] / decided
        if decided
        else 0.0
    )

    print("=" * 80)
    print("TTLB V2 HOLDOUT — CURRENT TEMPERANS")
    print("=" * 80)

    print(
        "HOLDOUT SHA:",
        "949bd51e1706c4d4933b92ac473ecd6c1aa20cb4a085360caa22a3c3f4cebeb5",
    )

    print("TOTAL:", metrics["total"])
    print("AUTO DECIDED:", decided)
    print(
        "ABSTAINED:",
        metrics["abstained"],
    )
    print(
        "AUTO COVERAGE:",
        round(coverage, 4),
    )
    print(
        "PRECISION DECIDED:",
        round(precision, 4),
    )
    print(
        "FALSE MERGES:",
        metrics["false_merges"],
    )
    print(
        "FALSE SPLITS:",
        metrics["false_splits"],
    )

    print()
    print("CATEGORY RESULTS")
    print("-" * 80)

    for name, m in sorted(
        by_category.items()
    ):
        coverage_c = (
            m["decided"] / m["total"]
            if m["total"]
            else 0.0
        )

        precision_c = (
            m["correct"] / m["decided"]
            if m["decided"]
            else 0.0
        )

        print(
            f"{name:28} "
            f"n={m['total']:3} "
            f"coverage={coverage_c:.3f} "
            f"precision={precision_c:.3f} "
            f"false_merges={m['false_merges']}"
        )

    print()
    print("MARGIN OBSERVATION ONLY")
    print("-" * 80)

    if margins:
        ordered = sorted(margins)

        print(
            "MIN:",
            round(ordered[0], 4),
        )

        print(
            "MEDIAN:",
            round(
                ordered[
                    len(ordered) // 2
                ],
                4,
            ),
        )

        print(
            "MAX:",
            round(ordered[-1], 4),
        )

    print()
    print("WRONG AUTO DECISIONS")
    print("-" * 80)

    if not failures:
        print("NONE")
    else:
        for failure in failures[:40]:
            print(
                failure["case_id"],
                "|",
                failure["category"],
                "| expected=",
                failure["expected"],
                "| candidate=",
                failure["expected_candidate"],
                "| decision=",
                failure["decision"],
                "| chosen=",
                failure["chosen_candidate"],
                "| margin=",
                round(
                    failure["margin"],
                    4,
                ),
            )


if __name__ == "__main__":
    main()
