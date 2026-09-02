import json
from pathlib import Path
import re
import time

from temperans.ttlb import (
    ATTACH,
    BRANCH,
    NEW,
    build_v0_cases,
)
from temperans.ttlb_eval import (
    Prediction,
    print_report,
)


class GeminiTrajectoryJudge:
    """
    Frontier-model semantic baseline for TTLB.

    Gemini reasons about linkage.
    Temperans still owns the benchmark, policy,
    state, calibration, and eventual routing.
    """

    def __init__(
        self,
        client,
        model="gemini-3.6-flash",
        max_attempts=3,
    ):
        self.client = client
        self.model = model
        self.max_attempts = max_attempts

    def _parse(self, text):
        text = text.strip()

        text = re.sub(
            r"^```(?:json)?\s*",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"\s*```$",
            "",
            text,
        )

        data = json.loads(text)

        label = str(
            data["label"]
        ).lower().strip()

        if label not in {
            ATTACH,
            BRANCH,
            NEW,
        }:
            raise ValueError(
                f"Invalid label: {label}"
            )

        confidence = float(
            data.get("confidence", 0.0)
        )

        evidence = data.get(
            "evidence",
            [],
        )

        return (
            label,
            confidence,
            evidence,
        )

    def predict(self, case):
        prompt = f"""
You are evaluating whether NEW WORK belongs to an
existing WORK TRAJECTORY.

This is NOT ordinary semantic similarity.

Possible labels:

ATTACH
The new work continues, repairs, refines, or reopens
the same underlying goal/problem.

BRANCH
The new work was caused by or clearly derives from
the existing trajectory, but starts a distinct goal
that should remain separately trackable.

NEW
The new work is a different goal/incident/task.
This includes cases that share the same topic,
project, repository, customer type, or vocabulary
but are actually distinct work.

Important principles:

- Goal continuity matters more than word overlap.
- Same topic does NOT imply same trajectory.
- Different wording can still represent the same
  evolving trajectory.
- Different concrete entities can be strong evidence
  against merging.
- A resolved issue recurring can be ATTACH/reopen.
- A lesson from one trajectory that creates a new
  objective can be BRANCH.
- Be conservative about merging.

EXISTING TRAJECTORY:

{case.candidate_text}

NEW WORK:

{case.new_text}

Return ONLY valid JSON:

{{
  "label": "attach|branch|new",
  "confidence": 0.0,
  "evidence": [
    "short reason",
    "short reason"
  ]
}}
"""

        last_error = None

        for attempt in range(
            1,
            self.max_attempts + 1,
        ):
            try:
                response = (
                    self.client.models.generate_content(
                        model=self.model,
                        contents=prompt,
                    )
                )

                return self._parse(
                    response.text or ""
                )

            except Exception as exc:
                last_error = exc

                if attempt < self.max_attempts:
                    time.sleep(attempt)

        raise RuntimeError(
            f"Gemini judge failed: {last_error}"
        )


def evaluate_gemini(
    judge,
    cases=None,
    checkpoint_path="ttlb_gemini_results.jsonl",
):
    cases = cases or build_v0_cases()

    checkpoint = Path(checkpoint_path)

    completed = {}

    if checkpoint.exists():
        for line in checkpoint.read_text().splitlines():
            if not line.strip():
                continue

            item = json.loads(line)
            completed[item["case_id"]] = item

    predictions = []

    for index, case in enumerate(cases, 1):
        if case.case_id in completed:
            item = completed[case.case_id]

            prediction = Prediction(
                case_id=case.case_id,
                expected=case.label,
                predicted=item["predicted"],
                score=float(item["confidence"]),
                correct=(
                    item["predicted"]
                    == case.label
                ),
                category=case.category,
                difficulty=case.difficulty,
            )

            predictions.append(prediction)

            print(
                f"Skipping {index}/{len(cases)} "
                f"{case.case_id} (checkpointed)"
            )

            continue

        print(
            f"Judging {index}/{len(cases)} "
            f"{case.case_id}..."
        )

        try:
            label, confidence, evidence = (
                judge.predict(case)
            )

        except Exception as exc:
            print()
            print("JUDGE INTERRUPTED")
            print("CASE:", case.case_id)
            print("ERROR:", exc)
            print()
            print(
                "Completed results are safely "
                f"stored in {checkpoint_path}"
            )
            print(
                "Rerun the same command later "
                "to resume."
            )

            break

        record = {
            "case_id": case.case_id,
            "expected": case.label,
            "predicted": label,
            "confidence": confidence,
            "evidence": evidence,
            "category": case.category,
            "difficulty": case.difficulty,
        }

        with checkpoint.open(
            "a",
            encoding="utf-8",
        ) as f:
            f.write(
                json.dumps(record)
                + "\n"
            )

        prediction = Prediction(
            case_id=case.case_id,
            expected=case.label,
            predicted=label,
            score=confidence,
            correct=(label == case.label),
            category=case.category,
            difficulty=case.difficulty,
        )

        predictions.append(prediction)

        print(
            "  expected=",
            case.label,
            " predicted=",
            label,
            " confidence=",
            round(confidence, 3),
        )

        for item in evidence:
            print("   -", item)

    return predictions


if __name__ == "__main__":
    from google import genai

    judge = GeminiTrajectoryJudge(
        client=genai.Client(),
    )

    predictions = evaluate_gemini(
        judge
    )

    print()
    print_report(predictions)
