from uuid import uuid4

from .events import Event
from .state import TrajectoryState
from .perception import PerceptionEngine


class Trace:

    def __init__(
        self,
        user_id=None,
        trajectory_id=None,
        conversation_id=None,
        thread_id=None,
        goal_id=None,
        store=None,
        behavior_model=None,
        thread_resolver=None,
        trajectory_router=None,
    ):
        self.user_id = user_id
        self.trajectory_id = trajectory_id or str(uuid4())
        self.conversation_id = conversation_id
        self.thread_id = thread_id
        self.goal_id = goal_id

        self.store = store
        self.behavior_model = behavior_model
        self.thread_resolver = thread_resolver
        self.trajectory_router = trajectory_router

        self.events = []
        self._state = TrajectoryState()
        self._perception = PerceptionEngine()

        if self.store is not None:
            old_events = self.store.load_events(
                self.trajectory_id
            )

            for event in old_events:
                self.events.append(event)

                self._state = self._perception.update(
                    self._state,
                    self.events,
                    event,
                )

                self._replay_behavior(event)

    def _previous_text(self):
        for event in reversed(self.events):
            if (
                event.text
                and event.actor_type in {"human", "agent"}
            ):
                return event.text

        return ""

    def _existing_threads(self):
        """
        Build semantic thread representations from
        persisted human AND agent text.

        Tool events are excluded because tool names/status
        are operational signals rather than natural-language
        descriptions of the thread.
        """

        result = {}

        for event in self.events:
            if (
                event.actor_type in {"human", "agent"}
                and event.thread_id
                and event.text
            ):
                result.setdefault(
                    event.thread_id,
                    [],
                ).append(event.text)

        return result

    def _resolve_thread(
        self,
        text,
        explicit_thread_id=None,
    ):
        # Explicit caller choice always wins.
        if explicit_thread_id:
            return (
                explicit_thread_id,
                None,
            )

        # Trace-level manual thread comes next.
        if self.thread_id:
            return (
                self.thread_id,
                None,
            )

        # New trajectory router.
        #
        # It operates over canonical events and decides:
        # ATTACH / SUGGEST / NEW.
        if self.trajectory_router is not None:
            result = self.trajectory_router.resolve(
                text=text,
                events=self.events,
            )

            return (
                result.thread_id,
                result,
            )

        # Legacy automatic thread resolver.
        if self.thread_resolver is not None:
            result = self.thread_resolver.resolve(
                text=text,
                existing_threads=self._existing_threads(),
            )

            return (
                result.thread_id,
                result,
            )

        return (
            None,
            None,
        )

    def _apply_behavior_dict(self, behavior):
        if not behavior:
            return

        primitive = behavior.get("primitive")

        self._state.last_behavior = primitive
        self._state.behavior_confidence = float(
            behavior.get("confidence", 0.0)
        )

        if primitive == "repair":
            self._state.repair_count += 1

        elif primitive == "refine":
            self._state.refinement_count += 1

        elif primitive == "new_topic":
            self._state.topic_switch_count += 1

        elif primitive == "clarify":
            self._state.clarification_count += 1

        elif primitive == "correct":
            self._state.correction_count += 1

        elif primitive == "resist":
            self._state.resistance_count += 1

        elif primitive == "disagree":
            self._state.disagreement_count += 1

    def _replay_behavior(self, event):
        behavior = event.metadata.get("behavior")

        if behavior:
            self._apply_behavior_dict(behavior)

    def observe(self, event):
        if event.conversation_id is None:
            event.conversation_id = self.conversation_id

        if event.thread_id is None:
            event.thread_id = self.thread_id

        if event.goal_id is None:
            event.goal_id = self.goal_id

        self.events.append(event)

        self._state = self._perception.update(
            self._state,
            self.events,
            event,
        )

        if self.store is not None:
            self.store.save_event(
                self.trajectory_id,
                self.user_id,
                event,
            )

        return event

    def human(
        self,
        text,
        actor_id=None,
        thread_id=None,
        goal_id=None,
        **metadata,
    ):
        previous_text = self._previous_text()

        resolved_thread_id, thread_result = (
            self._resolve_thread(
                text=text,
                explicit_thread_id=thread_id,
            )
        )

        event = Event(
            actor_type="human",
            actor_id=actor_id or self.user_id,
            text=text,
            conversation_id=self.conversation_id,
            thread_id=resolved_thread_id,
            goal_id=goal_id or self.goal_id,
            metadata=metadata,
        )

        if thread_result is not None:
            event.metadata["thread_resolution"] = (
                thread_result.to_dict()
            )

        if (
            self.behavior_model is not None
            and previous_text
        ):
            result = self.behavior_model.perceive(
                previous_text=previous_text,
                current_text=text,
            )

            event.metadata["behavior"] = (
                result.to_dict()
            )

        self.observe(event)
        self._replay_behavior(event)

        return event

    def agent(
        self,
        text,
        actor_id=None,
        thread_id=None,
        goal_id=None,
        **metadata,
    ):
        return self.observe(
            Event(
                actor_type="agent",
                actor_id=actor_id,
                text=text,
                thread_id=thread_id or self.thread_id,
                goal_id=goal_id or self.goal_id,
                metadata=metadata,
            )
        )

    def tool(
        self,
        name,
        status="success",
        thread_id=None,
        goal_id=None,
        **metadata,
    ):
        return self.observe(
            Event(
                actor_type="tool",
                tool_name=name,
                status=status,
                thread_id=thread_id or self.thread_id,
                goal_id=goal_id or self.goal_id,
                metadata=metadata,
            )
        )

    def query(self):
        from .query import TrajectoryQuery
        return TrajectoryQuery(self)

    def timeline(
        self,
        thread_id=None,
        goal_id=None,
    ):
        return self.query().timeline(
            thread_id=thread_id,
            goal_id=goal_id,
        )

    def failures(self):
        return self.query().failures()

    def repairs(self):
        return self.query().repairs()

    def resolutions(self):
        return self.query().resolutions()

    def agents(self):
        return self.query().agents()

    def threads(self):
        return self.query().threads()

    def goals(self):
        return self.query().goals()

    def summary(self):
        return self.query().summary()

    def analyze_trajectory(self, thread_id):
        from .trajectory import TrajectoryAnalyzer

        return TrajectoryAnalyzer(self).analyze(
            thread_id
        )

    def analyze_trajectories(self):
        from .trajectory import TrajectoryAnalyzer

        return TrajectoryAnalyzer(self).analyze_all()

    def state(self):
        return self._state.to_dict()
