from dataclasses import dataclass, field
import re


@dataclass
class ExtractedWorkState:
    goal: str
    current_problem: str
    entities: list = field(default_factory=list)
    artifacts: list = field(default_factory=list)


class WorkStateExtractor:
    """
    Pluggable extraction seam.

    V1 keeps caller-provided goal when available and otherwise
    derives a conservative fallback. This removes goal= as a hard
    API requirement without pretending the fallback is a mature
    semantic extractor.

    Replace with FrontierWorkStateExtractor / LocalExtractor later.
    """

    def extract(
        self,
        *,
        text,
        supplied_goal="",
        entities=None,
        artifacts=None,
        trajectory_context=None,
    ):
        text = " ".join(
            (text or "").strip().split()
        )

        goal = " ".join(
            (supplied_goal or "")
            .strip()
            .split()
        )

        if not goal:
            # Prefer the existing candidate's durable goal when
            # context is unambiguous.
            if (
                trajectory_context
                and len(
                    trajectory_context
                ) == 1
            ):
                goal = (
                    trajectory_context[0]
                    .get("goal", "")
                )

        if not goal:
            # Conservative raw fallback. This is intentionally
            # visible/auditable rather than pretending to infer a
            # durable objective perfectly.
            words = re.findall(
                r"[A-Za-z0-9_#.-]+",
                text,
            )
            goal = " ".join(
                words[:12]
            )

        return ExtractedWorkState(
            goal=goal,
            current_problem=text,
            entities=list(
                entities or []
            ),
            artifacts=list(
                artifacts or []
            ),
        )
