import ast
import json
import re
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from temperans.candidate_assessment import CandidateAssessment


class KimiCandidateAssessor:
    def __init__(
        self,
        api_key,
        model="kimi-k3",
        base_url="https://api.moonshot.ai/v1",
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    @staticmethod
    def _parse_object(content):
        content = (content or "").strip()

        if content.startswith("```"):
            lines = content.splitlines()
            if len(lines) >= 3:
                content = "\n".join(lines[1:-1]).strip()
                if content.lower().startswith("json"):
                    content = content[4:].lstrip()

        # First prefer valid JSON.
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Extract the outermost object if Kimi added prose.
        start = content.find("{")
        end = content.rfind("}")
        if start >= 0 and end > start:
            candidate = content[start:end + 1]
        else:
            candidate = content

        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

        # K3 may occasionally emit Python-style dict syntax despite JSON-only
        # prompting. literal_eval is intentionally used instead of eval.
        try:
            value = ast.literal_eval(candidate)
        except (ValueError, SyntaxError) as exc:
            preview = content[:1000]
            raise ValueError(
                "Kimi returned an unparsable assessment payload. "
                f"Raw content preview: {preview!r}"
            ) from exc

        if not isinstance(value, dict):
            raise ValueError(
                "Kimi assessment payload must decode to an object"
            )
        return value

    def assess(self, event, candidates):
        prompt = (
            "Assess whether each supplied candidate trajectory is the same "
            "underlying work as the incoming event. Return ONLY one object "
            'with key "assessments". Each assessment must contain '
            '"candidate_id", "same_work", "branch", "unrelated", '
            '"confidence", and "evidence". Scores must be numbers from 0 to 1. '
            "Never invent candidate IDs.\n"
            + json.dumps(
                {
                    "event": event,
                    "candidates": candidates,
                },
                sort_keys=True,
                ensure_ascii=False,
            )
        )

        body = {
            "model": self.model,
            "temperature": 1,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a trajectory relationship evaluator. "
                        "Return structured data only."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        }

        req = Request(
            self.base_url + "/chat/completions",
            data=json.dumps(body).encode(),
            method="POST",
            headers={
                "Authorization": "Bearer " + self.api_key,
                "Content-Type": "application/json",
            },
        )

        try:
            with urlopen(req, timeout=90) as response:
                raw = json.loads(response.read())
        except HTTPError as exc:
            detail = exc.read().decode(errors="replace")
            raise RuntimeError(
                f"Kimi API HTTP {exc.code}: {detail}"
            ) from exc

        content = raw["choices"][0]["message"].get("content", "")
        parsed = self._parse_object(content)

        valid = {
            item["trajectory_id"]
            for item in candidates
        }

        assessments = []
        for item in parsed.get("assessments", []):
            candidate_id = item.get("candidate_id")
            if candidate_id not in valid:
                continue

            assessments.append(
                CandidateAssessment(
                    candidate_id=candidate_id,
                    same_work=float(item["same_work"]),
                    branch=float(item["branch"]),
                    unrelated=float(item["unrelated"]),
                    confidence=float(item["confidence"]),
                    evidence=list(item.get("evidence", [])),
                )
            )

        return assessments, raw.get("usage", {})
