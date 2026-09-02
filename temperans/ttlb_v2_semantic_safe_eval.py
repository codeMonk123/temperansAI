import argparse
import json
from pathlib import Path

from temperans.anchors import AnchorExtractor
from temperans.frontier_judge import GeminiFrontierJudge
from temperans.semantic_safety_gate import SemanticSafetyGate
from temperans.workstate import ConversationState, TrajectoryState


DETERMINISTIC_CORRECT = 143
TOTAL_V2 = 250


def load_jsonl(path):
    p = Path(path)
    if not p.exists():
        return []

    return [
        json.loads(line)
        for line in p.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]


def load_abstentions(path):
    return {
        item["case_id"]: item
        for item in load_jsonl(path)
    }


def candidate_text(candidate):
    return " ".join(
        x
        for x in [
            candidate.get("goal", ""),
            candidate.get("state", ""),
            candidate.get("text", ""),
        ]
        if x
    )


def states(item, candidate):
    extractor = AnchorExtractor()

    trajectory = TrajectoryState(
        trajectory_id=candidate[
            "candidate_id"
        ],
        workspace_id="ttlb_v2",
        person_id="benchmark_user",
        durable_goal=candidate.get(
            "goal",
            "",
        ),
        current_state=candidate.get(
            "state",
            "",
        ),
        lifecycle=candidate.get(
            "lifecycle",
            "active",
        ),
        anchors=extractor.extract(
            candidate_text(candidate)
        ),
    )

    conversation = ConversationState(
        workspace_id="ttlb_v2",
        person_id="benchmark_user",
        conversation_id=(
            "incoming_" + item["case_id"]
        ),
        surface="benchmark",
        current_problem=item[
            "incoming_text"
        ],
        anchors=extractor.extract(
            item["incoming_text"]
        ),
    )

    return trajectory, conversation


def read_existing_raw_results(
    abstentions,
    semantic_cache_path,
):
    """
    Semantic Recovery V1's Gemini cache is signature-keyed and
    does not necessarily contain case IDs. Therefore this function
    also accepts the legacy evaluator output when case metadata was
    stored. Rows without a case_id cannot be safely mapped back to a
    benchmark case and are deliberately ignored.

    The live evaluator below writes a dedicated case-keyed cache so
    every future call is reusable.
    """

    mapped = {}

    for row in load_jsonl(
        semantic_cache_path
    ):
        case_id = row.get("case_id")

        if (
            case_id
            and case_id in abstentions
        ):
            mapped[case_id] = row

    return mapped


def load_case_cache(path):
    return {
        row["case_id"]: row
        for row in load_jsonl(path)
        if row.get("case_id")
    }


def append_case_cache(path, row):
    p = Path(path)
    p.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with p.open(
        "a",
        encoding="utf-8",
    ) as handle:
        handle.write(
            json.dumps(
                row,
                ensure_ascii=False,
            )
            + "\n"
        )


def evaluate_row(
    *,
    item,
    raw,
    gate,
):
    ranked = item[
        "ranked_candidates"
    ]

    top = ranked[0]

    second_score = (
        float(
            ranked[1][
                "semantic_score"
            ]
        )
        if len(ranked) > 1
        else None
    )

    trajectory, conversation = (
        states(item, top)
    )

    safe = gate.validate(
        frontier_decision=raw[
            "raw_decision"
        ],
        frontier_confidence=float(
            raw["raw_confidence"]
        ),
        candidate=trajectory,
        conversation=conversation,
        candidate_score=float(
            top["semantic_score"]
        ),
        second_score=second_score,
        is_top_candidate=True,
    )

    final = (
        safe.decision
        if safe.accepted
        else "clarify"
    )

    expected = item[
        "expected_decision"
    ]

    expected_candidate = item.get(
        "expected_candidate_id"
    )

    candidate_ok = True

    if (
        safe.accepted
        and expected
        in {"attach", "branch"}
        and expected_candidate
    ):
        candidate_ok = (
            safe.candidate_id
            == expected_candidate
        )

    correct_accepted = (
        safe.accepted
        and final == expected
        and candidate_ok
    )

    wrong_attach = (
        safe.accepted
        and final == "attach"
        and (
            expected != "attach"
            or not candidate_ok
        )
    )

    raw_correct = (
        raw["raw_decision"]
        == expected
        and (
            expected
            not in {
                "attach",
                "branch",
            }
            or expected_candidate
            == top["candidate_id"]
        )
    )

    return {
        "case_id":
            item["case_id"],
        "category":
            item["category"],
        "expected":
            expected,
        "expected_candidate":
            expected_candidate,
        "top_candidate":
            top["candidate_id"],
        "top_score":
            float(
                top[
                    "semantic_score"
                ]
            ),
        "second_score":
            second_score,
        "raw_decision":
            raw["raw_decision"],
        "raw_confidence":
            float(
                raw[
                    "raw_confidence"
                ]
            ),
        "raw_correct":
            raw_correct,
        "safe_decision":
            final,
        "safe_accepted":
            safe.accepted,
        "safe_confidence":
            safe.confidence,
        "safe_reasons":
            safe.reasons,
        "correct_accepted":
            correct_accepted,
        "wrong_attach":
            wrong_attach,
    }


def print_report(rows):
    evaluated = len(rows)

    raw_correct = sum(
        row["raw_correct"]
        for row in rows
    )

    raw_wrong_attach = sum(
        (
            row["raw_decision"]
            == "attach"
            and not row[
                "raw_correct"
            ]
        )
        for row in rows
    )

    accepted = sum(
        row["safe_accepted"]
        for row in rows
    )

    clarified = (
        evaluated - accepted
    )

    correct_accepted = sum(
        row["correct_accepted"]
        for row in rows
    )

    wrong_attach = sum(
        row["wrong_attach"]
        for row in rows
    )

    safe_precision = (
        correct_accepted / accepted
        if accepted
        else 0.0
    )

    safe_recovery_rate = (
        correct_accepted / evaluated
        if evaluated
        else 0.0
    )

    projected_auto = (
        DETERMINISTIC_CORRECT
        + correct_accepted
    )

    projected_coverage = (
        projected_auto / TOTAL_V2
    )

    print()
    print("=" * 72)
    print(
        "SAFE SEMANTIC RECOVERY STATUS"
    )
    print("=" * 72)

    print(
        "SEMANTIC CASES EVALUATED:",
        evaluated,
        "/ 107",
    )

    print()
    print("RAW FRONTIER")
    print(
        " correct:",
        raw_correct,
    )
    print(
        " wrong attaches:",
        raw_wrong_attach,
    )

    print()
    print("AFTER TEMPERANS SAFETY")
    print(
        " accepted:",
        accepted,
    )
    print(
        " clarified:",
        clarified,
    )
    print(
        " correct accepted:",
        correct_accepted,
    )
    print(
        " wrong accepted attaches:",
        wrong_attach,
    )
    print(
        " accepted precision:",
        round(
            safe_precision,
            4,
        ),
    )
    print(
        "safe recovery rate:",
        round(
            safe_recovery_rate,
            4,
        ),
    )

    print()
    print("PROJECTED END-TO-END")
    print(
        " deterministic correct:",
        DETERMINISTIC_CORRECT,
    )
    print(
        " + safe semantic correct:",
        correct_accepted,
    )
    print(
        " = automatic correct:",
        projected_auto,
        "/",
        TOTAL_V2,
    )
    print(
        " automatic coverage:",
        round(
            projected_coverage,
            4,
        ),
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--abstentions",
        default=(
            "ttlb_v2_semantic_abstentions.jsonl"
        ),
    )

    parser.add_argument(
        "--case-cache",
        default=(
            "ttlb_v2_semantic_safe_raw.jsonl"
        ),
    )

    parser.add_argument(
        "--legacy-cache",
        default=(
            "ttlb_v2_semantic_gemini_cache.jsonl"
        ),
    )

    parser.add_argument(
        "--max-new",
        type=int,
        default=0,
    )

    parser.add_argument(
        "--live",
        action="store_true",
    )

    args = parser.parse_args()

    abstentions = load_abstentions(
        args.abstentions
    )

    if len(abstentions) != 107:
        print(
            "WARNING: expected 107 "
            "deterministic abstentions, got",
            len(abstentions),
        )

    case_cache = load_case_cache(
        args.case_cache
    )

    legacy = (
        read_existing_raw_results(
            abstentions,
            args.legacy_cache,
        )
    )

    for case_id, row in legacy.items():
        case_cache.setdefault(
            case_id,
            row,
        )

    judge = None

    if args.live:
        from google import genai

        judge = GeminiFrontierJudge(
            client=genai.Client()
        )

    gate = SemanticSafetyGate()

    results = []
    new_calls = 0

    for case_id, item in (
        abstentions.items()
    ):
        raw = case_cache.get(
            case_id
        )

        if (
            raw is None
            and args.live
            and new_calls
            < args.max_new
        ):
            ranked = item[
                "ranked_candidates"
            ]

            top = ranked[0]

            second_score = (
                float(
                    ranked[1][
                        "semantic_score"
                    ]
                )
                if len(ranked) > 1
                else None
            )

            trajectory, conversation = (
                states(item, top)
            )

            print(
                "LIVE",
                case_id,
                "candidate=",
                top["candidate_id"],
            )

            try:
                decision = judge.judge(
                    trajectory=trajectory,
                    conversation=conversation,
                    structural_evidence={
                        "candidate_score":
                            float(
                                top[
                                    "semantic_score"
                                ]
                            ),
                        "second_score":
                            second_score,
                    },
                )
            except Exception as exc:
                print(
                    "INTERRUPTED:",
                    type(exc).__name__,
                    str(exc)[:400],
                )
                break

            raw = {
                "case_id":
                    case_id,
                "candidate_id":
                    top[
                        "candidate_id"
                    ],
                "raw_decision":
                    decision.decision,
                "raw_confidence":
                    decision.confidence,
                "raw_reasons":
                    decision.reasons,
            }

            append_case_cache(
                args.case_cache,
                raw,
            )

            case_cache[
                case_id
            ] = raw

            new_calls += 1

        if raw is None:
            continue

        result = evaluate_row(
            item=item,
            raw=raw,
            gate=gate,
        )

        results.append(
            result
        )

        print()
        print(
            result["case_id"],
            "expected=",
            result["expected"],
            "raw=",
            result[
                "raw_decision"
            ],
            "safe=",
            result[
                "safe_decision"
            ],
            "accepted=",
            result[
                "safe_accepted"
            ],
        )

        for reason in result[
            "safe_reasons"
        ]:
            print(" -", reason)

    print_report(results)

    print()
    print(
        "NEW LIVE CALLS:",
        new_calls,
    )


if __name__ == "__main__":
    main()
