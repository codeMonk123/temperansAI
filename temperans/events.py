from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Literal
from uuid import uuid4

ActorType = Literal["human", "agent", "tool"]


@dataclass
class Event:
    actor_type: ActorType
    text: str = ""

    actor_id: str | None = None
    conversation_id: str | None = None

    # Semantic organization
    thread_id: str | None = None
    goal_id: str | None = None

    tool_name: str | None = None
    status: str | None = None

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    event_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    timestamp: str = field(
        default_factory=lambda:
        datetime.now(timezone.utc).isoformat()
    )
