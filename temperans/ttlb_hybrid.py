import json

from temperans.ttlb import build_v0_cases
from temperans.hybrid_linker import (
    HybridTrajectoryLinker,
    UNCERTAIN,
)


def main():
    cases = build_v0_cases()

    with open(
        "ttlb_semantic_scores.json",
        "r",
        encoding="utf-8",
    ) as f:
        scores = {
            item["case_id"]: float(
                item["semantic_score"]
            )
            for item in json.load(f)
        }

    linker = HybridTrajectoryLinker()

    decided = 0
    correct_decided = 0
    abstained = 0
    false_merges = 0

    print("=" * 78)
    print("TEMPERANS HYBRID TTLB")
    print("=" * 78)

    for case in cases:
        # Observable trajectory state only.
        # Never derive linker inputs from the ground-truth label.
        unresolved = case.candidate_unresolved

        result = linker.decide(
            candidate_text=case.candidate_text,
            new_text=case.new_text,
            semantic_score=scores[case.case_id],
            trajectory_unresolved=unresolved,
        )

        if result.decision == UNCERTAIN:
            abstained += 1
            mark = "ABSTAIN"

        else:
            decided += 1

            if result.decision == case.label:
                correct_decided += 1
                mark = "PASS"
            else:
                mark = "FAIL"

                if (
                    result.decision == "attach"
                    and case.label != "attach"
                ):
                    false_merges += 1

        print(
            f"{mark:7} "
            f"{case.case_id:24} "
            f"expected={case.label:6} "
            f"decision={result.decision:9} "
            f"semantic={scores[case.case_id]:.4f}"
        )

    total = len(cases)

    coverage = (
        decided / total
        if total
        else 0.0
    )

    precision = (
        correct_decided / decided
        if decided
        else 0.0
    )

    print()
    print("=" * 78)
    print("SUMMARY")
    print("=" * 78)

    print("TOTAL:", total)
    print("DECIDED:", decided)
    print("ABSTAINED:", abstained)
    print("COVERAGE:", round(coverage, 4))
    print(
        "PRECISION ON DECIDED:",
        round(precision, 4),
    )
    print(
        "FALSE MERGES:",
        false_merges,
    )


if __name__ == "__main__":
    main()
