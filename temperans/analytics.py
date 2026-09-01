class ThreadAnalytics:

    def __init__(self, trace):
        self.trace = trace

    def analyze(self):
        threads = {}

        for event in self.trace.events:
            if not event.thread_id:
                continue

            item = threads.setdefault(
                event.thread_id,
                {
                    "events": 0,
                    "human_turns": 0,
                    "agent_turns": 0,
                    "tool_calls": 0,
                    "conversations": set(),
                    "repairs": 0,
                    "refinements": 0,
                    "failures": 0,
                    "successes": 0,
                },
            )

            item["events"] += 1

            if event.conversation_id:
                item["conversations"].add(
                    event.conversation_id
                )

            if event.actor_type == "human":
                item["human_turns"] += 1

                behavior = event.metadata.get(
                    "behavior", {}
                ).get("primitive")

                if behavior == "repair":
                    item["repairs"] += 1

                elif behavior == "refine":
                    item["refinements"] += 1

            elif event.actor_type == "agent":
                item["agent_turns"] += 1

            elif event.actor_type == "tool":
                item["tool_calls"] += 1

                if event.status == "failed":
                    item["failures"] += 1

                elif event.status == "success":
                    item["successes"] += 1

        result = {}

        for thread_id, item in threads.items():

            conversations = sorted(
                item["conversations"]
            )

            conversation_count = len(
                conversations
            )

            revisited = (
                conversation_count > 1
            )

            one_off = (
                conversation_count == 1
                and item["human_turns"] <= 1
            )

            result[thread_id] = {
                "events": item["events"],
                "human_turns": item["human_turns"],
                "agent_turns": item["agent_turns"],
                "tool_calls": item["tool_calls"],
                "conversations": conversations,
                "conversation_count":
                    conversation_count,
                "revisited": revisited,
                "one_off": one_off,
                "repairs": item["repairs"],
                "refinements":
                    item["refinements"],
                "failures": item["failures"],
                "successes": item["successes"],
            }

        return result
