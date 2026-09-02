from dataclasses import dataclass, field


@dataclass
class CanonicalPilotEvent:
    organization_id: str
    workspace_id: str
    surface: str
    external_user_id: str
    conversation_id: str
    text: str
    goal: str = ""
    entities: list = field(default_factory=list)
    artifacts: list = field(default_factory=list)
    properties: dict = field(default_factory=dict)


class EventAdapter:
    """
    Adapter contract for arbitrary organization payloads.
    """

    def normalize(
        self,
        *,
        organization_id,
        payload,
    ):
        raise NotImplementedError


class GenericChatbotAdapter(EventAdapter):
    def normalize(
        self,
        *,
        organization_id,
        payload,
    ):
        return CanonicalPilotEvent(
            organization_id=
                organization_id,
            workspace_id=
                payload.get(
                    "workspace_id",
                    "default",
                ),
            surface=
                payload.get(
                    "surface",
                    "generic_chatbot",
                ),
            external_user_id=
                payload[
                    "external_user_id"
                ],
            conversation_id=
                payload[
                    "conversation_id"
                ],
            text=
                payload[
                    "message"
                ],
            goal=
                payload.get(
                    "goal",
                    "",
                ),
            entities=
                payload.get(
                    "entities",
                    [],
                ),
            artifacts=
                payload.get(
                    "artifacts",
                    [],
                ),
            properties=
                payload.get(
                    "properties",
                    {},
                ),
        )
