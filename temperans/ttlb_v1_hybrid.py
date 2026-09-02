import json
from collections import defaultdict

from temperans.ttlb_v1 import build_v1
from temperans.hybrid_linker import (
    HybridTrajectoryLinker,
    UNCERTAIN,
)


def main():
    cases = build_v1()

    with open(
        "ttlb_v1_semantic_scores.json",
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

    total = len(cases)
    decided = 0
    correct = 0
    abstained = 0
    false_merges = 0

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

    for case in cases:
        score = scores[case.case_id]

        result = linker.decide(
            candidate_text=case.candidate_text(),
            new_text=case.new_text,
            semantic_score=score,
            trajectory_unresolved=(
                case.candidate_unresolved
            ),
        )

        bucket = by_category[case.category]
        bucket["total"] += 1

        if result.decision == UNCERTAIN:
            abstained += 1
            bucket["abstained"] += 1
            continue

        decided += 1
        bucket["decided"] += 1

        if result.decision == case.label:
            correct += 1
            bucket["correct"] += 1

        else:
            failures.append(
                (
                    case.case_id,
                    case.category,
                    case.label,
                    result.decision,
                    score,
                )
            )

            if (
                result.decision == "attach"
                and case.label != "attach"
            ):
                false_merges += 1
                bucket["false_merges"] += 1

    coverage = decided / total

    precision = (
        correct / decided
        if decided
        else 0.0
    )

    print("=" * 78)
    print("TTLB V1 — TEMPERANS HYBRID V0")
    print("=" * 78)

    print("TOTAL:", total)
    print("DECIDED:", decided)
    print("ABSTAINED:", abstained)
    print("COVERAGE:", round(coverage, 4))
    print(
        "PRECISION ON DECIDED:",
        round(precision, 4),
    )
    print("FALSE MERGES:", false_merges)

    print()
    print("CATEGORY RESULTS")
    print("-" * 78)

    for category, m in sorted(
        by_category.items()
    ):
        category_coverage = (
            m["decided"] / m["total"]
            if m["total"]
            else 0.0
        )

        category_precision = (
            m["correct"] / m["decided"]
            if m["decided"]
            else 0.0
        )

        print(
            f"{category:32} "
            f"n={m['total']:3} "
            f"coverage={category_coverage:.3f} "
            f"precision={category_precision:.3f} "
            f"false_merges={m['false_merges']}"
        )

    print()
    print("WRONG DECISIONS")
    print("-" * 78)

    if not failures:
        print("NONE")
    else:
        for failure in failures[:30]:
            print(
                failure[0],
                "|",
                failure[1],
                "| expected=",
                failure[2],
                "| decision=",
                failure[3],
                "| semantic=",
                round(failure[4], 4),
            )


if __name__ == "__main__":
    main()
