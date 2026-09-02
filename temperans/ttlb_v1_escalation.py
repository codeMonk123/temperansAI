import json

from temperans.ttlb_v1 import build_v1
from temperans.ttlb_v1_structured import build_states
from temperans.structured_linker import (
    StructuredTrajectoryLinker,
    UNCERTAIN,
)
from temperans.linkage import LinkageEvidenceExtractor


def main():
    cases = build_v1()

    with open(
        "ttlb_v1_semantic_scores.json",
        "r",
        encoding="utf-8",
    ) as f:
        scores = {
            x["case_id"]: float(
                x["semantic_score"]
            )
            for x in json.load(f)
        }

    linker = StructuredTrajectoryLinker()
    language = LinkageEvidenceExtractor()

    escalation = []

    for case in cases:
        trajectory, conversation = build_states(
            case
        )

        language_evidence = language.extract(
            candidate_text=case.candidate_text(),
            new_text=case.new_text,
        )

        local = linker.decide(
            trajectory=trajectory,
            conversation=conversation,
            semantic_score=scores[case.case_id],
            branch_signal=(
                language_evidence.has_branch_signal
            ),
            continuation_signal=(
                language_evidence.has_continuation_signal
            ),
        )

        if local.decision != UNCERTAIN:
            continue

        escalation.append({
            "case_id": case.case_id,

            # Ground truth is stored for evaluation only.
            # It must never be supplied to the judge.
            "expected": case.label,
            "category": case.category,

            "semantic_score": scores[
                case.case_id
            ],

            "trajectory": {
                "durable_goal":
                    trajectory.durable_goal,
                "current_state":
                    trajectory.current_state,
                "lifecycle":
                    trajectory.lifecycle,
                "entities":
                    trajectory.entities,
                "artifacts":
                    trajectory.artifacts,
                "open_questions":
                    trajectory.open_questions,
                "recent_context":
                    trajectory.recent_context,
            },

            "conversation": {
                "goal":
                    conversation.goal,
                "current_problem":
                    conversation.current_problem,
                "intent":
                    conversation.intent,
                "entities":
                    conversation.entities,
                "artifacts":
                    conversation.artifacts,
                "unresolved":
                    conversation.unresolved,
            },

            "structural_evidence":
                local.evidence.to_dict(),
        })

    with open(
        "ttlb_v1_escalation.jsonl",
        "w",
        encoding="utf-8",
    ) as f:
        for item in escalation:
            f.write(
                json.dumps(item)
                + "\n"
            )

    print("TOTAL TTLB:", len(cases))
    print(
        "LOCAL DECIDED:",
        len(cases) - len(escalation),
    )
    print(
        "ESCALATION:",
        len(escalation),
    )
    print(
        "ESCALATION RATE:",
        round(
            len(escalation) / len(cases),
            4,
        ),
    )
    print()
    print(
        "SAVED: ttlb_v1_escalation.jsonl"
    )


if __name__ == "__main__":
    main()
