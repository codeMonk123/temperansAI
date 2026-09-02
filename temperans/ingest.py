from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Optional
import uuid


VALID_EVENT_TYPES = {
    "human_message",
    "agent_message",
    "tool_call",
    "tool_result",
    "product_event",
    "business_event",
    "feedback",
    "outcome",
}


@dataclass
class CanonicalEvent:
    """
    Provider-independent Temperans ingestion contract.

    Any chatbot, agent, collaboration tool, or product
    can emit this event without understanding trajectory
    routing internals.
    """

    workspace_id: str
    surface: str
    conversation_id: str
    event_type: str

    surface_user_id: Optional[str] = None
    person_id: Optional[str] = None
    actor_id: Optional[str] = None

    text: str = ""

    entities: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)

    properties: dict[str, Any] = field(default_factory=dict)

    event_id: str = field(
        default_factory=lambda: (
            "evt_" + uuid.uuid4().hex[:16]
        )
    )

    timestamp: str = field(
        default_factory=lambda: (
            datetime.now(timezone.utc).isoformat()
        )
    )

    def __post_init__(self):
        if self.event_type not in VALID_EVENT_TYPES:
            raise ValueError(
                f"Unsupported event_type: {self.event_type}"
            )

    def to_dict(self):
        return asdict(self)


class TemperansIngest:
    """
    Universal V0 ingestion surface.

    Later this will feed identity resolution,
    ConversationState extraction and trajectory routing.
    """

    def __init__(self, identity_resolver=None):
        self.identity_resolver = identity_resolver

    def observe(
        self,
        *,
        workspace_id,
        surface,
        conversation_id,
        event_type,
        text="",
        surface_user_id=None,
        person_id=None,
        actor_id=None,
        entities=None,
        artifacts=None,
        properties=None,
    ):
        resolved_person = person_id

        if (
            resolved_person is None
            and self.identity_resolver is not None
            and surface_user_id
        ):
            resolved_person = (
                self.identity_resolver.resolve(
                    workspace_id=workspace_id,
                    surface=surface,
                    surface_user_id=surface_user_id,
                )
            )

            if resolved_person is None:
                resolved_person = (
                    self.identity_resolver
                    .anonymous_person_id(
                        workspace_id=workspace_id,
                        surface=surface,
                        surface_user_id=surface_user_id,
                    )
                )

        return CanonicalEvent(
            workspace_id=workspace_id,
            surface=surface,
            conversation_id=conversation_id,
            event_type=event_type,
            surface_user_id=surface_user_id,
            person_id=resolved_person,
            actor_id=actor_id,
            text=text,
            entities=list(entities or []),
            artifacts=list(artifacts or []),
            properties=dict(properties or {}),
        )

    def human_message(self, **kwargs):
        return self.observe(
            event_type="human_message",
            **kwargs,
        )

    def agent_message(self, **kwargs):
        return self.observe(
            event_type="agent_message",
            **kwargs,
        )

    def product_event(self, **kwargs):
        return self.observe(
            event_type="product_event",
            **kwargs,
        )
