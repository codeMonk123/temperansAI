from pathlib import Path

from temperans.event_adapter import GenericChatbotAdapter
from temperans.identity_registry import IdentityRegistry
from temperans.pilot_service import PilotService
from temperans.sqlite_audit_store import SQLitePilotAuditStore
from temperans.policy import PolicyRegistry
from temperans.sqlite_store import SQLiteStore, EventConflict
from temperans.workstate_extractor_v1 import WorkStateExtractor
from temperans.late_events import classify_late_event


# Compatibility name used by partner_api.
IdempotencyConflict = EventConflict


class OrganizationRuntime:
    def __init__(self, *, root, config, adapter=None, extractor=None, policies=None):
        self.platform_root = Path(root)
        self.root = self.platform_root / "organizations" / config.organization_id
        self.root.mkdir(parents=True, exist_ok=True)
        self.config = config
        self.adapter = adapter or GenericChatbotAdapter()
        self.extractor = extractor or WorkStateExtractor()
        self.policies = policies or PolicyRegistry()
        self.policy = self.policies.get(config.policy_id)

        self.sqlite = SQLiteStore(self.platform_root / "control" / "control.db")
        self.service = PilotService(
            self.root,
            audit_store=SQLitePilotAuditStore(
                self.sqlite,
                config.organization_id,
            ),
        )

        self.identities = IdentityRegistry(
            organization_id=config.organization_id,
            store=self.sqlite,
        )

    def observe(self, payload):
        event_id = payload.event_id if hasattr(payload, "event_id") else payload.get("event_id")
        if not event_id:
            raise ValueError("event_id is required")

        # Normalize before persistence so useful canonical fields are promoted.
        event = self.adapter.normalize(
            organization_id=self.config.organization_id,
            payload=payload,
        )

        surface_policy = self.policy.allow_surface(self.config, event.surface)
        if not surface_policy.allowed:
            raise PermissionError(surface_policy.reason)

        person_id = self.identities.resolve(
            event.workspace_id,
            event.surface,
            event.external_user_id,
            True,
        )

        late = classify_late_event(
            self.sqlite, self.config.organization_id, event
        )
        stored = self.sqlite.insert_event(
            organization_id=self.config.organization_id,
            event_id=event_id,
            payload=(
                payload.storage_payload()
                if hasattr(payload, "storage_payload")
                else payload
            ),
            workspace_id=event.workspace_id,
            person_id=person_id,
            external_user_id=event.external_user_id,
            conversation_id=event.conversation_id,
            surface=event.surface,
            event_type=event.type,
            occurred_at=event.occurred_at,
            source_sequence=event.source_sequence,
            late_event=late["late_event"],
        )

        # Completed duplicate: return the original result before any mutation.
        if stored["result"] is not None:
            return stored["result"]

        candidates = self.service.trajectories(
            event.workspace_id,
            person_id,
        )

        work = self.extractor.extract(
            text=event.text,
            supplied_goal=event.goal,
            entities=event.entities,
            artifacts=event.artifacts,
        )

        result = self.service.observe({
            "workspace_id": event.workspace_id,
            "person_id": person_id,
            "external_user_id": event.external_user_id,
            "conversation_id": event.conversation_id,
            "surface": event.surface,
            "goal": work.goal,
            "current_problem": work.current_problem,
            "entities": work.entities,
            "artifacts": work.artifacts,
            "anchors": work.anchors,
            "properties": event.metadata,
        }, event_id=event_id)

        result["organization_id"] = self.config.organization_id
        result["person_id"] = person_id
        result["event_id"] = event_id
        result.update(late)

        self.sqlite.complete_event(
            organization_id=self.config.organization_id,
            event_id=event_id,
            result=result,
        )
        return result

    def link_identity(self, *, workspace_id, surface, external_user_id, person_id):
        return self.identities.link(
            workspace_id,
            surface,
            external_user_id,
            person_id,
        )
