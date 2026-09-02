from dataclasses import dataclass, asdict
import json
import re
import time


ATTACH = "attach"
BRANCH = "branch"
NEW = "new"
UNCERTAIN = "uncertain"

VALID = {ATTACH, BRANCH, NEW, UNCERTAIN}


@dataclass
class FrontierDecision:
    decision: str
    confidence: float
    reasons: list

    def to_dict(self):
        return asdict(self)


class FrontierTrajectoryJudge:
    """
    Provider-neutral trajectory reasoning interface.

    Frontier models provide semantic reasoning.
    Temperans owns state, retrieval, evidence,
    calibration and final routing policy.
    """

    def judge(
        self,
        trajectory,
        conversation,
        structural_evidence=None,
    ):
        raise NotImplementedError


class GeminiFrontierJudge(FrontierTrajectoryJudge):

    def __init__(
        self,
        client,
        model="gemini-3.6-flash",
        max_attempts=2,
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

        decision = str(
            data["decision"]
        ).lower().strip()

        if decision not in VALID:
            raise ValueError(
                f"Invalid decision: {decision}"
            )

        return FrontierDecision(
            decision=decision,
            confidence=float(
                data.get("confidence", 0.0)
            ),
            reasons=[
                str(x)
                for x in data.get("reasons", [])
            ],
        )

    def judge(
        self,
        trajectory,
        conversation,
        structural_evidence=None,
    ):
        prompt = f"""
You are a trajectory-linkage judge for Temperans.

The question is NOT whether two pieces of text are
semantically similar.

Determine whether NEW WORK belongs to the same
evolving work trajectory as the CANDIDATE TRAJECTORY.

Labels:

ATTACH
The new work continues, progresses, repairs, refines,
or reopens the same underlying work objective.

BRANCH
The new work clearly derives from the existing work,
but starts a distinct objective that should remain
separately trackable.

NEW
The new work is a distinct goal/task/incident even if
it shares the same project, repository, customer type,
topic, vocabulary, or technology.

UNCERTAIN
There is genuinely insufficient evidence to decide
safely.

Important:

- Same project does NOT mean same trajectory.
- Same repository does NOT mean same trajectory.
- High semantic similarity does NOT prove identity.
- Different wording can represent the same evolving work.
- State progression matters.
- A resolved issue recurring can be ATTACH.
- Prefer UNCERTAIN over an unsafe merge.

CANDIDATE TRAJECTORY:

durable_goal:
{trajectory.durable_goal}

current_state:
{trajectory.current_state}

lifecycle:
{trajectory.lifecycle}

entities:
{trajectory.entities}

artifacts:
{trajectory.artifacts}

open_questions:
{trajectory.open_questions}

recent_context:
{trajectory.recent_context}


NEW WORK:

goal:
{conversation.goal}

current_problem:
{conversation.current_problem}

intent:
{conversation.intent}

entities:
{conversation.entities}

artifacts:
{conversation.artifacts}

unresolved:
{conversation.unresolved}


STRUCTURAL EVIDENCE:

{structural_evidence or {}}


Return ONLY JSON:

{{
  "decision": "attach|branch|new|uncertain",
  "confidence": 0.0,
  "reasons": [
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
            f"Frontier judge failed: {last_error}"
        )
