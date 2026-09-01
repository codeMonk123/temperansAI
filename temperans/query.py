class TrajectoryQuery:

    def __init__(self, trace):
        self.trace = trace

    def _filtered_events(
        self,
        thread_id=None,
        goal_id=None,
    ):
        events = self.trace.events

        if thread_id is not None:
            events = [
                e for e in events
                if e.thread_id == thread_id
            ]

        if goal_id is not None:
            events = [
                e for e in events
                if e.goal_id == goal_id
            ]

        return events

    def timeline(
        self,
        thread_id=None,
        goal_id=None,
    ):
        events = self._filtered_events(
            thread_id=thread_id,
            goal_id=goal_id,
        )

        return [
            {
                "event_id": e.event_id,
                "conversation_id": e.conversation_id,
                "thread_id": e.thread_id,
                "goal_id": e.goal_id,
                "actor_type": e.actor_type,
                "actor_id": e.actor_id,
                "text": e.text,
                "tool_name": e.tool_name,
                "status": e.status,
                "behavior": e.metadata.get("behavior"),
                "timestamp": e.timestamp,
            }
            for e in events
        ]

    def failures(self):
        return [
            e for e in self.trace.events
            if (
                e.actor_type == "tool"
                and e.status == "failed"
            )
        ]

    def repairs(self):
        return [
            e for e in self.trace.events
            if (
                e.actor_type == "human"
                and e.metadata.get(
                    "behavior", {}
                ).get("primitive") == "repair"
            )
        ]

    def resolutions(self):
        events = self.trace.events
        results = []

        for i, event in enumerate(events):
            if (
                event.actor_type == "tool"
                and event.status == "success"
            ):
                previous_agent = None

                for prior in reversed(events[:i]):
                    if prior.actor_type == "agent":
                        previous_agent = prior
                        break

                results.append({
                    "tool_event": event,
                    "agent_event": previous_agent,
                    "thread_id": event.thread_id,
                    "goal_id": event.goal_id,
                })

        return results

    def agents(self):
        result = {}

        for event in self.trace.events:
            if (
                event.actor_type == "agent"
                and event.actor_id
            ):
                result.setdefault(
                    event.actor_id,
                    {
                        "events": 0,
                        "tool_failures_after": 0,
                        "tool_successes_after": 0,
                    },
                )

                result[
                    event.actor_id
                ]["events"] += 1

        current_agent = None

        for event in self.trace.events:
            if (
                event.actor_type == "agent"
                and event.actor_id
            ):
                current_agent = event.actor_id

            elif (
                event.actor_type == "tool"
                and current_agent in result
            ):
                if event.status == "failed":
                    result[
                        current_agent
                    ][
                        "tool_failures_after"
                    ] += 1

                elif event.status == "success":
                    result[
                        current_agent
                    ][
                        "tool_successes_after"
                    ] += 1

        return result

    def threads(self):
        result = {}

        for event in self.trace.events:
            if not event.thread_id:
                continue

            item = result.setdefault(
                event.thread_id,
                {
                    "events": 0,
                    "conversations": set(),
                    "goals": set(),
                    "human_events": 0,
                    "agent_events": 0,
                    "tool_events": 0,
                },
            )

            item["events"] += 1

            if event.conversation_id:
                item["conversations"].add(
                    event.conversation_id
                )

            if event.goal_id:
                item["goals"].add(
                    event.goal_id
                )

            key = (
                event.actor_type
                + "_events"
            )

            if key in item:
                item[key] += 1

        # Convert sets for clean public output.
        for item in result.values():
            item["conversations"] = sorted(
                item["conversations"]
            )
            item["goals"] = sorted(
                item["goals"]
            )

        return result

    def goals(self):
        result = {}

        for event in self.trace.events:
            if not event.goal_id:
                continue

            item = result.setdefault(
                event.goal_id,
                {
                    "events": 0,
                    "threads": set(),
                    "conversations": set(),
                },
            )

            item["events"] += 1

            if event.thread_id:
                item["threads"].add(
                    event.thread_id
                )

            if event.conversation_id:
                item["conversations"].add(
                    event.conversation_id
                )

        for item in result.values():
            item["threads"] = sorted(
                item["threads"]
            )
            item["conversations"] = sorted(
                item["conversations"]
            )

        return result

    def summary(self):
        state = self.trace.state()

        return {
            "trajectory_id":
                self.trace.trajectory_id,

            "events":
                state["event_count"],

            "conversations":
                state["conversation_count"],

            "agents":
                state["agent_count"],

            "threads":
                len(self.threads()),

            "goals":
                len(self.goals()),

            "repairs":
                state["repair_count"],

            "tool_failures":
                state["tool_failures"],

            "cross_agent_duplicates":
                state[
                    "cross_agent_duplicate_actions"
                ],

            "agent_handoffs":
                state["agent_handoffs"],

            "recoveries":
                state["recovery_count"],

            "resolved":
                not state["unresolved"],
        }
