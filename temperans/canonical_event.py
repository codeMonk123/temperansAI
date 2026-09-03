"""CanonicalEvent V1: provider-independent ingestion contract."""
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone

def utc_now():
    return datetime.now(timezone.utc).isoformat()

@dataclass(frozen=True)
class CanonicalEvent:
    organization_id:str
    event_id:str
    workspace_id:str
    surface:str
    external_user_id:str
    conversation_id:str
    type:str="human_message"
    occurred_at:str|None=None
    received_at:str|None=None
    source_sequence:str|None=None
    content:dict=field(default_factory=dict)
    goal:str=""
    entities:list=field(default_factory=list)
    artifacts:list=field(default_factory=list)
    metadata:dict=field(default_factory=dict)

    @property
    def text(self):
        return str((self.content or {}).get("text",""))

    def to_dict(self):
        x=asdict(self)
        if x["received_at"] is None:x["received_at"]=utc_now()
        return x

    def storage_payload(self):
        # Stable logical payload: received_at is transport metadata and is not
        # part of idempotency identity.
        x=self.to_dict()
        x.pop("received_at",None)
        return x
