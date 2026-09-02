from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class ConversationState:
    """
    Provider-independent interpretation of one conversation/work event.
    """

    workspace_id: str
    person_id: str
    conversation_id: str
    surface: str

    goal: str = ""
    current_problem: str = ""
    intent: str = ""

    entities: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)

    decisions: list[str] = field(default_factory=list)
    attempts: list[str] = field(default_factory=list)
    unresolved: list[str] = field(default_factory=list)
    outcomes: list[str] = field(default_factory=list)

    timestamp: Optional[str] = None

    def to_dict(self):
        return asdict(self)

    def retrieval_text(self):
        values = [
            self.goal,
            self.current_problem,
            self.intent,
            *self.entities,
            *self.artifacts,
            *self.unresolved,
        ]

        return " ".join(
            str(value).strip()
            for value in values
            if str(value).strip()
        )


@dataclass
class TrajectoryState:
    """
    Evolving state of one piece of work.

    This is the durable object Temperans carries across surfaces.
    """

    trajectory_id: str
    workspace_id: str
    person_id: str

    durable_goal: str = ""
    current_state: str = ""
    lifecycle: str = "active"

    entities: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)

    open_questions: list[str] = field(default_factory=list)
    resolved_questions: list[str] = field(default_factory=list)

    decisions: list[str] = field(default_factory=list)
    attempts: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)
    outcomes: list[str] = field(default_factory=list)

    surfaces: list[str] = field(default_factory=list)
    conversation_ids: list[str] = field(default_factory=list)

    recent_context: list[str] = field(default_factory=list)

    def _append_unique(self, target, values):
        for value in values:
            if value and value not in target:
                target.append(value)

    def apply(self, state: ConversationState):
        """
        Apply a linked ConversationState to this trajectory.
        """

        if not self.durable_goal and state.goal:
            self.durable_goal = state.goal

        if state.current_problem:
            self.current_state = state.current_problem

        self._append_unique(
            self.entities,
            state.entities,
        )

        self._append_unique(
            self.artifacts,
            state.artifacts,
        )

        self._append_unique(
            self.decisions,
            state.decisions,
        )

        self._append_unique(
            self.attempts,
            state.attempts,
        )

        self._append_unique(
            self.open_questions,
            state.unresolved,
        )

        self._append_unique(
            self.outcomes,
            state.outcomes,
        )

        self._append_unique(
            self.surfaces,
            [state.surface],
        )

        self._append_unique(
            self.conversation_ids,
            [state.conversation_id],
        )

        if state.current_problem:
            self.recent_context.append(
                state.current_problem
            )

            self.recent_context = (
                self.recent_context[-8:]
            )

        return self

    def to_dict(self):
        return asdict(self)

    def retrieval_text(self):
        values = [
            self.durable_goal,
            self.current_state,
            *self.entities,
            *self.artifacts,
            *self.open_questions,
            *self.recent_context,
        ]

        return " ".join(
            str(value).strip()
            for value in values
            if str(value).strip()
        )
