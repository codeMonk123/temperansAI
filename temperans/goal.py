from dataclasses import dataclass, asdict
import json
import re
import time


@dataclass
class SemanticGoalState:
    domain: str
    goal: str
    intent: str
    entities: list
    issue: str
    stage: str
    extractor: str = "unknown"

    def to_dict(self):
        return asdict(self)

    def routing_text(self):
        parts = [
            self.domain,
            self.goal,
            self.intent,
            self.issue,
            self.stage,
            " ".join(self.entities),
        ]

        return " ".join(
            part.strip()
            for part in parts
            if part and part.strip()
        )


class LocalGoalStateExtractor:
    """
    Cheap fail-open extractor.

    This is deliberately simple. Its job is to ensure
    routing never blocks because an external model failed.
    """

    def extract(self, text):
        clean = " ".join(text.strip().split())
        lower = clean.lower()

        if any(
            x in lower
            for x in [
                "deploy",
                "production",
                "container",
                "environment variable",
                "startup",
            ]
        ):
            domain = "software deployment"
            goal = "restore production service"
            intent = "debug"

        elif any(
            x in lower
            for x in [
                "robotics",
                "autonomous systems",
                "master's",
                "masters",
                "graduate program",
            ]
        ):
            domain = "graduate education"
            goal = "find suitable robotics graduate program"
            intent = "research"

        elif any(
            x in lower
            for x in [
                "benchmark",
                "evaluation",
                "shuffled history",
                "trajectory",
            ]
        ):
            domain = "AI evaluation"
            goal = "evaluate trajectory understanding"
            intent = "evaluate"

        else:
            domain = "general"
            goal = clean[:160]
            intent = "other"

        tokens = re.findall(
            r"[A-Za-z0-9_.-]+",
            lower,
        )

        stop = {
            "the", "and", "that", "this", "with",
            "what", "should", "about", "after",
            "from", "have", "were", "was", "now",
            "but", "our", "your", "into",
        }

        entities = []

        for token in tokens:
            if (
                len(token) >= 5
                and token not in stop
                and token not in entities
            ):
                entities.append(token)

        return SemanticGoalState(
            domain=domain,
            goal=goal,
            intent=intent,
            entities=entities[:10],
            issue=clean[:160],
            stage="unknown",
            extractor="local_fallback",
        )


class GeminiGoalStateExtractor:
    """
    Gemini normalizes language into GoalState.

    Temperans owns the routing decision.

    If Gemini is temporarily unavailable, extraction
    falls back locally rather than blocking ingestion.
    """

    def __init__(
        self,
        client,
        model="gemini-3.6-flash",
        max_attempts=3,
        fallback=None,
    ):
        self.client = client
        self.model = model
        self.max_attempts = max_attempts

        self.fallback = (
            fallback or LocalGoalStateExtractor()
        )

        self.cache = {}

    def _parse_json(self, text):
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

        return SemanticGoalState(
            domain=str(
                data.get("domain", "")
            ).strip(),
            goal=str(
                data.get("goal", "")
            ).strip(),
            intent=str(
                data.get("intent", "")
            ).strip(),
            entities=[
                str(x).strip()
                for x in data.get(
                    "entities",
                    [],
                )
                if str(x).strip()
            ][:10],
            issue=str(
                data.get("issue", "")
            ).strip(),
            stage=str(
                data.get("stage", "")
            ).strip(),
            extractor="gemini",
        )

    def extract(self, text):
        key = text.strip()

        if key in self.cache:
            return self.cache[key]

        prompt = """
Normalize the user's message into a compact goal state.

Return ONLY valid JSON with this schema:

{
  "domain": "broad stable domain",
  "goal": "durable outcome the user is trying to achieve",
  "intent": "debug|research|build|evaluate|decide|learn|other",
  "entities": ["important specific entities"],
  "issue": "current problem or question",
  "stage": "current stage of the work"
}

Rules:

- Normalize different wording for the same underlying goal
  into similar domain and goal descriptions.
- Goal describes the durable objective, not just the sentence.
- Do not invent unsupported facts.
- Keep strings concise.

User message:

""" + key

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

                state = self._parse_json(
                    response.text or ""
                )

                self.cache[key] = state
                return state

            except Exception as exc:
                last_error = exc

                if attempt < self.max_attempts:
                    time.sleep(attempt)

        state = self.fallback.extract(key)

        self.cache[key] = state

        return state
