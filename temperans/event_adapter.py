from temperans.canonical_event import CanonicalEvent

class EventAdapter:
    def normalize(self,*,organization_id,payload):
        raise NotImplementedError

class GenericChatbotAdapter(EventAdapter):
    """Accepts both legacy message payloads and CanonicalEvent-shaped payloads."""
    def normalize(self,*,organization_id,payload):
        if isinstance(payload,CanonicalEvent):
            if payload.organization_id!=organization_id:
                raise ValueError("organization mismatch")
            return payload
        content=payload.get("content")
        if content is None:
            content={"text":payload.get("message","")}
        if not isinstance(content,dict):
            raise ValueError("content must be an object")
        return CanonicalEvent(
            organization_id=organization_id,
            event_id=payload["event_id"],
            workspace_id=payload.get("workspace_id","default"),
            surface=payload.get("surface","generic_chatbot"),
            external_user_id=payload["external_user_id"],
            conversation_id=payload["conversation_id"],
            type=payload.get("type","human_message"),
            occurred_at=payload.get("occurred_at"),
            received_at=payload.get("received_at"),
            source_sequence=payload.get("source_sequence"),
            content=content,
            goal=payload.get("goal",""),
            entities=list(payload.get("entities",[])),
            artifacts=list(payload.get("artifacts",[])),
            metadata=dict(payload.get("metadata",payload.get("properties",{}))),
        )

CanonicalPilotEvent=CanonicalEvent
