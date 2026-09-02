import json
import re
from collections import defaultdict

from temperans.ttlb_v1 import build_v1
from temperans.workstate import (
    ConversationState,
    TrajectoryState,
)
from temperans.structured_linker import (
    StructuredTrajectoryLinker,
    UNCERTAIN,
)
from temperans.linkage import LinkageEvidenceExtractor


def infer_incoming_entities(case):
    """
    TTLB adapter only.

    In production these come from ConversationState extraction,
    not benchmark-specific parsing.
    """

    entities = []

    # Customer identifiers.
    for match in re.findall(
        r"\bcustomer_\d+\b",
        case.new_text,
        flags=re.IGNORECASE,
    ):
        entities.append(match.lower())

    # If the candidate's named entity is explicitly repeated
    # in the new text, preserve it.
    lower = case.new_text.lower()

    for entity in case.candidate_entities:
        if entity.lower() in lower:
            entities.append(entity.lower())

    return list(dict.fromkeys(entities))


def infer_incoming_artifacts(case):
    """
    TTLB adapter only.

    Production extraction will produce typed artifacts.
    """

    artifacts = []
    lower = case.new_text.lower()

    for artifact in case.candidate_artifacts:
        if artifact.lower() in lower:
            artifacts.append(artifact.lower())

    # Repository phrasing in generated TTLB cases.
    match = re.search(
        r"\brepository\s+([a-zA-Z0-9_.-]+)",
        case.new_text,
        flags=re.IGNORECASE,
    )

    if match:
        artifacts.append(
            match.group(1).lower()
        )

    return list(dict.fromkeys(artifacts))


def build_states(case):
    trajectory = TrajectoryState(
        trajectory_id=(
            "candidate_" + case.case_id
        ),
        workspace_id="ttlb",
        person_id="benchmark_user",
        durable_goal=case.candidate_goal,
        current_state=case.candidate_state,
        lifecycle=case.candidate_lifecycle,
        entities=list(
            case.candidate_entities
        ),
        artifacts=list(
            case.candidate_artifacts
        ),
    )

    conversation = ConversationState(
        workspace_id="ttlb",
        person_id="benchmark_user",
        conversation_id=(
            "incoming_" + case.case_id
        ),
        surface="benchmark",
        # Do NOT derive goal from ground truth.
        # V1 leaves semantic interpretation to the
        # embedding/frontier layer.
        goal="",
        current_problem=case.new_text,
        entities=infer_incoming_entities(
            case
        ),
        artifacts=infer_incoming_artifacts(
            case
        ),
    )

    return trajectory, conversation


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

    linker = StructuredTrajectoryLinker()
    language = LinkageEvidenceExtractor()

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

    wrong = []

    for case in cases:
        trajectory, conversation = (
            build_states(case)
        )

        # Linguistic evidence is independent of
        # ground-truth label.
        language_evidence = language.extract(
            candidate_text=(
                case.candidate_text()
            ),
            new_text=case.new_text,
        )

        result = linker.decide(
            trajectory=trajectory,
            conversation=conversation,
            semantic_score=scores[
                case.case_id
            ],
            branch_signal=(
                language_evidence
                .has_branch_signal
            ),
            continuation_signal=(
                language_evidence
                .has_continuation_signal
            ),
        )

        bucket = by_category[
            case.category
        ]

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
            wrong.append(
                (
                    case.case_id,
                    case.category,
                    case.label,
                    result.decision,
                    scores[case.case_id],
                )
            )

            if (
                result.decision == "attach"
                and case.label != "attach"
            ):
                false_merges += 1
                bucket[
                    "false_merges"
                ] += 1

    coverage = decided / total

    precision = (
        correct / decided
        if decided
        else 0.0
    )

    print("=" * 80)
    print(
        "TTLB V1 — STRUCTURED TEMPERANS LINKER"
    )
    print("=" * 80)

    print("TOTAL:", total)
    print("DECIDED:", decided)
    print("ABSTAINED:", abstained)
    print(
        "COVERAGE:",
        round(coverage, 4),
    )
    print(
        "PRECISION ON DECIDED:",
        round(precision, 4),
    )
    print(
        "FALSE MERGES:",
        false_merges,
    )

    print()
    print("CATEGORY RESULTS")
    print("-" * 80)

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
    print("-" * 80)

    if not wrong:
        print("NONE")
    else:
        for item in wrong[:40]:
            print(
                item[0],
                "|",
                item[1],
                "| expected=",
                item[2],
                "| decision=",
                item[3],
                "| semantic=",
                round(item[4], 4),
            )


if __name__ == "__main__":
    main()
