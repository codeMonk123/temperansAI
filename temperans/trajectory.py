from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class TrajectoryAnalysis:
    thread_id: str

    conversation_count: int
    human_turns: int
    agent_turns: int
    tool_calls: int

    providers: List[str]
    agent_ids: List[str]

    revisited: bool
    one_off: bool

    continuity: float
    evolution: float

    repairs: int
    refinements: int
    corrections: int

    failures: int
    successes: int
    recoveries: int

    state: str

    evidence: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TrajectoryAnalyzer:

    def __init__(self, trace):
        self.trace = trace

    def _events(self, thread_id):
        return [
            event
            for event in self.trace.events
            if event.thread_id == thread_id
        ]

    def _semantic_scores(self, events):
        texts = [
            event.text.strip()
            for event in events
            if (
                event.actor_type == "human"
                and event.text
                and event.text.strip()
            )
        ]

        if len(texts) <= 1:
            return 0.0, 0.0

        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words="english",
        )

        try:
            X = vectorizer.fit_transform(texts)
        except ValueError:
            return 0.0, 0.0

        similarities = []

        for i in range(1, len(texts)):
            score = cosine_similarity(
                X[i - 1],
                X[i],
            )[0][0]

            similarities.append(float(score))

        if not similarities:
            return 0.0, 0.0

        continuity = sum(similarities) / len(
            similarities
        )

        # V0 interpretation:
        #
        # continuity = lexical/semantic similarity
        # evolution  = amount of change while remaining
        #              inside the same discovered thread
        #
        # This is NOT a calibrated scientific score yet.
        evolution = 1.0 - continuity

        return (
            round(continuity, 4),
            round(evolution, 4),
        )

    def analyze(
        self,
        thread_id: str,
    ) -> Optional[TrajectoryAnalysis]:

        events = self._events(thread_id)

        if not events:
            return None

        conversations = sorted({
            event.conversation_id
            for event in events
            if event.conversation_id
        })

        human_events = [
            event
            for event in events
            if event.actor_type == "human"
        ]

        agent_events = [
            event
            for event in events
            if event.actor_type == "agent"
        ]

        tool_events = [
            event
            for event in events
            if event.actor_type == "tool"
        ]

        # Preserve trajectory order.
        providers = []
        for event in events:
            provider = event.metadata.get("provider")

            if (
                provider
                and provider not in providers
            ):
                providers.append(provider)

        agent_ids = []
        for event in agent_events:
            if (
                event.actor_id
                and event.actor_id not in agent_ids
            ):
                agent_ids.append(event.actor_id)

        repairs = 0
        refinements = 0
        corrections = 0

        for event in human_events:
            primitive = (
                event.metadata
                .get("behavior", {})
                .get("primitive")
            )

            if primitive == "repair":
                repairs += 1
            elif primitive == "refine":
                refinements += 1
            elif primitive == "correct":
                corrections += 1

        failures = sum(
            1
            for event in tool_events
            if event.status == "failed"
        )

        successes = sum(
            1
            for event in tool_events
            if event.status == "success"
        )

        continuity, evolution = (
            self._semantic_scores(events)
        )

        conversation_count = len(conversations)
        revisited = conversation_count > 1

        one_off = (
            conversation_count == 1
            and len(human_events) <= 1
        )

        # Thread-local recovery:
        # at least one failure followed later by success.
        recoveries = 0
        seen_failure = False

        for event in tool_events:
            if event.status == "failed":
                seen_failure = True

            elif (
                event.status == "success"
                and seen_failure
            ):
                recoveries += 1
                seen_failure = False

        if one_off:
            state = "one_off"

        elif failures > 0 and successes == 0:
            state = "stalled"

        elif recoveries > 0:
            state = "recovered"

        elif revisited:
            state = "evolving"

        else:
            state = "active"

        evidence = []

        if revisited:
            evidence.append(
                f"revisited across "
                f"{conversation_count} conversations"
            )

        if one_off:
            evidence.append(
                "observed in only one conversation"
            )

        if len(providers) > 1:
            evidence.append(
                "cross-provider trajectory: "
                + " -> ".join(providers)
            )

        if repairs:
            evidence.append(
                f"{repairs} repair transition(s)"
            )

        if refinements:
            evidence.append(
                f"{refinements} refinement transition(s)"
            )

        if corrections:
            evidence.append(
                f"{corrections} correction transition(s)"
            )

        if failures:
            evidence.append(
                f"{failures} failed tool action(s)"
            )

        if recoveries:
            evidence.append(
                f"{recoveries} recovery event(s)"
            )

        if len(human_events) > 1:
            evidence.append(
                f"continuity={continuity:.3f}, "
                f"evolution={evolution:.3f}"
            )

        return TrajectoryAnalysis(
            thread_id=thread_id,

            conversation_count=conversation_count,
            human_turns=len(human_events),
            agent_turns=len(agent_events),
            tool_calls=len(tool_events),

            providers=providers,
            agent_ids=agent_ids,

            revisited=revisited,
            one_off=one_off,

            continuity=continuity,
            evolution=evolution,

            repairs=repairs,
            refinements=refinements,
            corrections=corrections,

            failures=failures,
            successes=successes,
            recoveries=recoveries,

            state=state,

            evidence=evidence,
        )

    def analyze_all(self):
        thread_ids = []

        for event in self.trace.events:
            if (
                event.thread_id
                and event.thread_id
                not in thread_ids
            ):
                thread_ids.append(
                    event.thread_id
                )

        return {
            thread_id: self.analyze(thread_id)
            for thread_id in thread_ids
        }
