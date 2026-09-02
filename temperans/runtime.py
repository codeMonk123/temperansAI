from dataclasses import dataclass, asdict
import uuid

from temperans.workstate import (
    ConversationState,
    TrajectoryState,
)
from temperans.context_pack import ContextPackBuilder


@dataclass
class TemperansResult:
    decision: str
    trajectory_id: str
    source: str
    confidence: float
    context_pack: dict

    def to_dict(self):
        return asdict(self)


class TemperansRuntime:
    """
    Universal Temperans orchestration layer.

    V0 intentionally accepts an already-created
    ConversationState. Semantic extraction from raw
    CanonicalEvent text is plugged in next.

    This keeps:
      ingestion
      semantic interpretation
      trajectory identity
    as separate components.
    """

    def __init__(
        self,
        cascade_linker,
        semantic_scorer=None,
        candidate_floor=0.15,
    ):
        self.cascade_linker = cascade_linker
        self.semantic_scorer = semantic_scorer
        self.candidate_floor = candidate_floor

        # V0 in-memory state.
        # Persistent storage replaces this next.
        self.trajectories = {}

        self.context_builder = (
            ContextPackBuilder()
        )

    def _new_trajectory_id(self):
        return (
            "traj_"
            + uuid.uuid4().hex[:12]
        )

    def _semantic_score(
        self,
        trajectory,
        conversation,
    ):
        if self.semantic_scorer is None:
            return 0.0

        return float(
            self.semantic_scorer(
                trajectory,
                conversation,
            )
        )

    def _create_trajectory(
        self,
        conversation,
    ):
        trajectory = TrajectoryState(
            trajectory_id=(
                self._new_trajectory_id()
            ),
            workspace_id=(
                conversation.workspace_id
            ),
            person_id=conversation.person_id,
            durable_goal=conversation.goal,
            current_state=(
                conversation.current_problem
            ),
            lifecycle="active",
        )

        trajectory.apply(conversation)

        self.trajectories[
            trajectory.trajectory_id
        ] = trajectory

        return trajectory

    def process(
        self,
        conversation: ConversationState,
    ):
        candidates = [
            trajectory
            for trajectory
            in self.trajectories.values()
            if (
                trajectory.workspace_id
                == conversation.workspace_id
                and trajectory.person_id
                == conversation.person_id
            )
        ]

        # First work observed for this person.
        if not candidates:
            trajectory = (
                self._create_trajectory(
                    conversation
                )
            )

            pack = self.context_builder.build(
                trajectory
            )

            return TemperansResult(
                decision="new",
                trajectory_id=(
                    trajectory.trajectory_id
                ),
                source="temperans_runtime",
                confidence=1.0,
                context_pack=pack.to_dict(),
            )

        # Candidate retrieval happens BEFORE linkage.
        #
        # If nothing is even plausibly related, this is new work.
        # Do not ask the linker/frontier/user to choose among
        # irrelevant trajectories.
        scored_candidates = [
            (
                self._semantic_score(
                    trajectory,
                    conversation,
                ),
                trajectory,
            )
            for trajectory in candidates
        ]

        best_candidate_score = max(
            score
            for score, _ in scored_candidates
        )

        if best_candidate_score < self.candidate_floor:
            trajectory = self._create_trajectory(
                conversation
            )

            pack = self.context_builder.build(
                trajectory
            )

            return TemperansResult(
                decision="new",
                trajectory_id=trajectory.trajectory_id,
                source="candidate_retrieval",
                confidence=0.90,
                context_pack=pack.to_dict(),
            )

        ranked = []

        for score, trajectory in scored_candidates:
            decision = (
                self.cascade_linker.decide(
                    trajectory=trajectory,
                    conversation=conversation,
                    semantic_score=score,
                )
            )

            ranked.append(
                (
                    decision.confidence,
                    trajectory,
                    decision,
                )
            )

        ranked.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        _, trajectory, decision = (
            ranked[0]
        )

        if decision.decision == "attach":
            trajectory.apply(
                conversation
            )

        elif decision.decision == "branch":
            parent = trajectory

            trajectory = (
                self._create_trajectory(
                    conversation
                )
            )

            # V0 relationship metadata.
            trajectory.recent_context.insert(
                0,
                (
                    "branched from "
                    + parent.trajectory_id
                ),
            )

        elif decision.decision == "new":
            trajectory = (
                self._create_trajectory(
                    conversation
                )
            )

        # CLARIFY deliberately does NOT mutate
        # either candidate or create a new trajectory.
        if decision.decision == "clarify":
            pack = self.context_builder.build(
                trajectory
            )

            return TemperansResult(
                decision="clarify",
                trajectory_id=(
                    trajectory.trajectory_id
                ),
                source=decision.source,
                confidence=decision.confidence,
                context_pack=pack.to_dict(),
            )

        pack = self.context_builder.build(
            trajectory
        )

        return TemperansResult(
            decision=decision.decision,
            trajectory_id=(
                trajectory.trajectory_id
            ),
            source=decision.source,
            confidence=decision.confidence,
            context_pack=pack.to_dict(),
        )
