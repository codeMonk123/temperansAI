import argparse
import json
import time
from pathlib import Path

from temperans.frontier_judge import (
    GeminiFrontierJudge,
)
from temperans.workstate import (
    ConversationState,
    TrajectoryState,
)


def load_jsonl(path):
    with open(path, "r", encoding="utf-8") as f:
        return [
            json.loads(line)
            for line in f
            if line.strip()
        ]


def build_states(item):
    t = item["trajectory"]
    c = item["conversation"]

    trajectory = TrajectoryState(
        trajectory_id="candidate_" + item["case_id"],
        workspace_id="ttlb",
        person_id="benchmark_user",
        durable_goal=t.get("durable_goal", ""),
        current_state=t.get("current_state", ""),
        lifecycle=t.get("lifecycle", "active"),
        entities=t.get("entities", []),
        artifacts=t.get("artifacts", []),
        open_questions=t.get("open_questions", []),
        recent_context=t.get("recent_context", []),
    )

    conversation = ConversationState(
        workspace_id="ttlb",
        person_id="benchmark_user",
        conversation_id="incoming_" + item["case_id"],
        surface="benchmark",
        goal=c.get("goal", ""),
        current_problem=c.get("current_problem", ""),
        intent=c.get("intent", ""),
        entities=c.get("entities", []),
        artifacts=c.get("artifacts", []),
        unresolved=c.get("unresolved", []),
    )

    return trajectory, conversation


def load_completed(path):
    completed = {}

    if not path.exists():
        return completed

    for line in path.read_text().splitlines():
        if line.strip():
            item = json.loads(line)
            completed[item["case_id"]] = item

    return completed


def print_report(sample, completed):
    evaluated = [
        completed[item["case_id"]]
        for item in sample
        if item["case_id"] in completed
    ]

    if not evaluated:
        print()
        print("No completed frontier cases yet.")
        return

    correct = sum(
        x["predicted"] == x["expected"]
        for x in evaluated
    )

    false_merges = sum(
        x["predicted"] == "attach"
        and x["expected"] != "attach"
        for x in evaluated
    )

    uncertain = sum(
        x["predicted"] == "uncertain"
        for x in evaluated
    )

    confident = [
        x for x in evaluated
        if x["confidence"] >= 0.80
        and x["predicted"] != "uncertain"
    ]

    confident_correct = sum(
        x["predicted"] == x["expected"]
        for x in confident
    )

    print()
    print("=" * 72)
    print("FRONTIER SAMPLE STATUS")
    print("=" * 72)

    print(
        "COMPLETED:",
        len(evaluated),
        "/",
        len(sample),
    )

    print(
        "ACCURACY:",
        round(correct / len(evaluated), 4),
    )

    print(
        "FALSE MERGES:",
        false_merges,
    )

    print(
        "UNCERTAIN:",
        uncertain,
    )

    print(
        "CONFIDENT DECISIONS:",
        len(confident),
    )

    if confident:
        print(
            "CONFIDENT PRECISION:",
            round(
                confident_correct / len(confident),
                4,
            ),
        )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input",
        default="ttlb_v1_frontier_sample.jsonl",
    )

    parser.add_argument(
        "--output",
        default="ttlb_v1_frontier_gemini_results.jsonl",
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=3.0,
    )

    parser.add_argument(
        "--max-new",
        type=int,
        default=20,
    )

    args = parser.parse_args()

    sample = load_jsonl(args.input)

    output = Path(args.output)

    completed = load_completed(output)

    from google import genai

    judge = GeminiFrontierJudge(
        client=genai.Client(),
    )

    newly_completed = 0

    for index, item in enumerate(sample, 1):
        case_id = item["case_id"]

        if case_id in completed:
            print(
                f"SKIP {index}/{len(sample)} "
                f"{case_id}"
            )
            continue

        if newly_completed >= args.max_new:
            break

        trajectory, conversation = (
            build_states(item)
        )

        print()
        print(
            f"JUDGE {index}/{len(sample)} "
            f"{case_id}"
        )

        try:
            result = judge.judge(
                trajectory=trajectory,
                conversation=conversation,
                structural_evidence=item.get(
                    "structural_evidence",
                    {},
                ),
            )

        except Exception as exc:
            print("INTERRUPTED:", type(exc).__name__)
            print(str(exc)[:500])
            print()
            print(
                "All completed cases are checkpointed."
            )
            break

        record = {
            "case_id": case_id,

            # Evaluation field; never supplied to judge.
            "expected": item["expected"],

            "category": item["category"],
            "predicted": result.decision,
            "confidence": result.confidence,
            "reasons": result.reasons,
        }

        with output.open(
            "a",
            encoding="utf-8",
        ) as f:
            f.write(
                json.dumps(record)
                + "\n"
            )

        completed[case_id] = record
        newly_completed += 1

        print("EXPECTED:", item["expected"])
        print("PREDICTED:", result.decision)
        print("CONFIDENCE:", result.confidence)

        for reason in result.reasons:
            print("-", reason)

        if args.delay:
            time.sleep(args.delay)

    print_report(
        sample,
        completed,
    )


if __name__ == "__main__":
    main()
