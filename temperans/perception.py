from .events import Event
from .state import TrajectoryState


class PerceptionEngine:

    def update(
        self,
        state: TrajectoryState,
        events: list[Event],
        event: Event,
    ) -> TrajectoryState:

        state.event_count += 1

        if event.conversation_id:
            state.conversations.add(
                event.conversation_id
            )

        if event.actor_type == "human":
            state.human_events += 1

        elif event.actor_type == "agent":
            state.agent_events += 1

            if event.actor_id:
                if (
                    state.last_agent_id
                    and state.last_agent_id
                    != event.actor_id
                ):
                    state.agent_handoffs += 1

                state.agents.add(event.actor_id)
                state.last_agent_id = event.actor_id

        elif event.actor_type == "tool":
            state.tool_events += 1

            previous_tools = [
                e for e in events[:-1]
                if e.actor_type == "tool"
            ]

            if previous_tools:
                previous = previous_tools[-1]

                if (
                    previous.tool_name
                    == event.tool_name
                    and previous.metadata
                    == event.metadata
                ):
                    state.duplicate_tool_calls += 1

                    previous_agent = self._agent_before(
                        events,
                        previous.event_id,
                    )

                    current_agent = self._agent_before(
                        events,
                        event.event_id,
                    )

                    if (
                        previous_agent
                        and current_agent
                        and previous_agent.actor_id
                        != current_agent.actor_id
                    ):
                        state.cross_agent_duplicate_actions += 1

                if (
                    previous.tool_name
                    and event.tool_name
                    and previous.tool_name
                    != event.tool_name
                ):
                    state.tool_switches += 1

            if event.status == "failed":
                state.tool_failures += 1
                state.consecutive_tool_failures += 1
                state.unresolved = True
                state.recovered = False

            elif event.status == "success":
                if state.unresolved:
                    state.recovery_count += 1
                    state.recovered = True

                state.consecutive_tool_failures = 0
                state.unresolved = False

            state.last_tool_name = event.tool_name

        return state

    def _agent_before(
        self,
        events,
        event_id,
    ):
        result = None

        for event in events:
            if event.event_id == event_id:
                break

            if event.actor_type == "agent":
                result = event

        return result
