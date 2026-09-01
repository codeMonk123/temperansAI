from dataclasses import dataclass, field


@dataclass
class TrajectoryState:
    event_count: int = 0
    human_events: int = 0
    agent_events: int = 0
    tool_events: int = 0

    conversations: set = field(default_factory=set)
    agents: set = field(default_factory=set)

    tool_failures: int = 0
    consecutive_tool_failures: int = 0
    duplicate_tool_calls: int = 0
    cross_agent_duplicate_actions: int = 0

    agent_handoffs: int = 0
    tool_switches: int = 0
    recovery_count: int = 0

    unresolved: bool = False
    recovered: bool = False

    last_agent_id: str | None = None
    last_tool_name: str | None = None

    # Behavioral trajectory
    last_behavior: str | None = None
    behavior_confidence: float = 0.0

    repair_count: int = 0
    refinement_count: int = 0
    topic_switch_count: int = 0
    clarification_count: int = 0
    correction_count: int = 0
    resistance_count: int = 0
    disagreement_count: int = 0

    def to_dict(self):
        return {
            "event_count": self.event_count,
            "human_events": self.human_events,
            "agent_events": self.agent_events,
            "tool_events": self.tool_events,

            "conversation_count": len(self.conversations),
            "agent_count": len(self.agents),

            "tool_failures": self.tool_failures,
            "consecutive_tool_failures":
                self.consecutive_tool_failures,
            "duplicate_tool_calls":
                self.duplicate_tool_calls,
            "cross_agent_duplicate_actions":
                self.cross_agent_duplicate_actions,

            "agent_handoffs": self.agent_handoffs,
            "tool_switches": self.tool_switches,
            "recovery_count": self.recovery_count,

            "unresolved": self.unresolved,
            "recovered": self.recovered,

            "last_agent_id": self.last_agent_id,
            "last_tool_name": self.last_tool_name,

            "last_behavior": self.last_behavior,
            "behavior_confidence": self.behavior_confidence,

            "repair_count": self.repair_count,
            "refinement_count": self.refinement_count,
            "topic_switch_count": self.topic_switch_count,
            "clarification_count": self.clarification_count,
            "correction_count": self.correction_count,
            "resistance_count": self.resistance_count,
            "disagreement_count": self.disagreement_count,
        }
