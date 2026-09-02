from dataclasses import dataclass, asdict
from typing import Optional

from temperans.workstate import TrajectoryState


@dataclass
class ContextPack:
    trajectory_id: str

    goal: str
    current_state: str
    lifecycle: str

    entities: list
    artifacts: list

    open_questions: list
    decisions: list
    attempts: list
    failures: list
    outcomes: list

    recent_context: list

    def to_dict(self):
        return asdict(self)

    def to_prompt(self):
        """
        Compact provider-independent context that can be
        supplied to any AI/agent after trajectory routing.
        """

        sections = []

        def add(title, value):
            if not value:
                return

            sections.append(title)

            if isinstance(value, list):
                for item in value:
                    sections.append(
                        f"- {item}"
                    )
            else:
                sections.append(str(value))

            sections.append("")

        add("WORK GOAL", self.goal)
        add("CURRENT STATE", self.current_state)
        add("LIFECYCLE", self.lifecycle)

        add("IMPORTANT ENTITIES", self.entities)
        add("RELEVANT ARTIFACTS", self.artifacts)

        add(
            "OPEN / UNRESOLVED",
            self.open_questions,
        )

        add("DECISIONS", self.decisions)
        add("ALREADY TRIED", self.attempts)
        add("FAILURES", self.failures)
        add("OUTCOMES", self.outcomes)

        add(
            "RECENT EVOLUTION",
            self.recent_context,
        )

        return "\n".join(sections).strip()


class ContextPackBuilder:
    """
    Builds the portable state that follows work
    across models/surfaces.
    """

    def build(
        self,
        trajectory: TrajectoryState,
    ) -> ContextPack:
        return ContextPack(
            trajectory_id=trajectory.trajectory_id,

            goal=trajectory.durable_goal,
            current_state=trajectory.current_state,
            lifecycle=trajectory.lifecycle,

            entities=list(trajectory.entities),
            artifacts=list(trajectory.artifacts),

            open_questions=list(
                trajectory.open_questions
            ),

            decisions=list(
                trajectory.decisions
            ),

            attempts=list(
                trajectory.attempts
            ),

            failures=list(
                trajectory.failures
            ),

            outcomes=list(
                trajectory.outcomes
            ),

            recent_context=list(
                trajectory.recent_context[-6:]
            ),
        )
