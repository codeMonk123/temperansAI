from pathlib import Path

from temperans.event_adapter import GenericChatbotAdapter
from temperans.identity_registry import IdentityRegistry
from temperans.pilot_service import PilotService
from temperans.sqlite_audit_store import SQLitePilotAuditStore
from temperans.policy import PolicyRegistry
from temperans.sqlite_store import SQLiteStore, EventConflict
from temperans.workstate_extractor_v1 import WorkStateExtractor
from temperans.late_events import classify_late_event
from temperans.runtime_support import RuntimeSignalSupport, instrumentation
from temperans.concurrency_recovery import observe_with_concurrency_recovery
from temperans.routing_control import apply_routing_mode


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

        self.signal_support = RuntimeSignalSupport(
            self.sqlite, config.organization_id
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

        service_payload = {
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
        }
        mode = getattr(self.config, "routing_mode", "automatic")
        if mode == "clarify_only":
            proposal = self.service.propose(service_payload)
            proposed_tid = proposal.get("trajectory_id")
            base_version = None
            if proposed_tid:
                base = self.sqlite.get_trajectory(
                    organization_id=self.config.organization_id,
                    trajectory_id=proposed_tid)
                if base is not None:
                    base_version = base["trajectory_version"]
            pending = self.sqlite.create_pending_proposal(
                organization_id=self.config.organization_id,
                event_id=event_id,
                proposed_decision=proposal.get("decision"),
                proposed_trajectory_id=proposed_tid,
                service_payload=service_payload,
                proposal=proposal,
                base_trajectory_version=base_version)
            result=dict(proposal)
            result.update({"proposed_decision":proposal.get("decision"),
                           "decision":"clarify","requires_confirmation":True,
                           "routing_mode":mode,"proposal_id":pending["proposal_id"]})
        else:
            result = observe_with_concurrency_recovery(
                self.service, service_payload, event_id, max_retries=1)

        result["organization_id"] = self.config.organization_id
        result["person_id"] = person_id
        result["event_id"] = event_id
        if mode != "clarify_only":
            result = apply_routing_mode(mode, result)
        result.update(late)

        trajectory_row = (
            self.sqlite.get_trajectory(
                organization_id=self.config.organization_id,
                trajectory_id=result.get("trajectory_id"),
            )
            if result.get("trajectory_id") else None
        )
        trajectory_state = trajectory_row["state"] if trajectory_row else {}
        delta_row = (
            None if mode == "clarify_only" else
            self.sqlite.conn.execute(
                "SELECT state_delta_json FROM decisions WHERE organization_id=? AND event_id=? ORDER BY created_at DESC LIMIT 1",
                (self.config.organization_id, event_id)).fetchone()
        )
        import json
        state_delta = json.loads(delta_row["state_delta_json"]) if delta_row else {}
        signals, signal_ids = self.signal_support.record(
            event_id, result.get("trajectory_id"), state_delta, trajectory_state
        )
        result["signals"] = signals
        result["signal_ids"] = signal_ids
        result["instrumentation"] = instrumentation(
            result,
            trajectory_row["trajectory_version"] if trajectory_row else None,
        )

        self.sqlite.complete_event(
            organization_id=self.config.organization_id,
            event_id=event_id,
            result=result,
        )
        return result

    def reject_proposal(self, proposal_id):
        row = self.sqlite.get_pending_proposal(organization_id=self.config.organization_id, proposal_id=proposal_id)
        if row is None: raise KeyError("proposal not found")
        if row["status"] == "rejected": return row
        if row["status"] != "pending": raise ValueError("proposal is not pending")
        return self.sqlite.resolve_pending_proposal(organization_id=self.config.organization_id, proposal_id=proposal_id, status="rejected")

    def confirm_proposal(self, proposal_id):
        row = self.sqlite.get_pending_proposal(organization_id=self.config.organization_id, proposal_id=proposal_id)
        if row is None: raise KeyError("proposal not found")
        if row["status"] == "confirmed": return row
        if row["status"] != "pending": raise ValueError("proposal is not pending")
        proposed_decision=row["proposed_decision"]
        proposed_tid=row["proposed_trajectory_id"]
        if proposed_tid and row["base_trajectory_version"] is not None:
            current=self.sqlite.get_trajectory(organization_id=self.config.organization_id, trajectory_id=proposed_tid)
            if current is None or current["trajectory_version"] != row["base_trajectory_version"]:
                return self.sqlite.resolve_pending_proposal(organization_id=self.config.organization_id, proposal_id=proposal_id, status="stale")
        service_payload = dict(row["service_payload"])

        # Pending proposals cross a JSON persistence boundary. Re-run the
        # canonical extractor so anchors are restored as typed Anchor objects
        # instead of persisted JSON dictionaries/strings.
        work = self.extractor.extract(
            text=service_payload.get("current_problem", ""),
            supplied_goal=service_payload.get("goal", ""),
            entities=service_payload.get("entities", []),
            artifacts=service_payload.get("artifacts", []),
        )
        service_payload["goal"] = work.goal
        service_payload["current_problem"] = work.current_problem
        service_payload["entities"] = work.entities
        service_payload["artifacts"] = work.artifacts
        service_payload["anchors"] = work.anchors

        fresh=self.service.propose(service_payload)
        same_proposal = fresh.get("decision") == proposed_decision
        # NEW proposals create a fresh synthetic trajectory id on every
        # non-mutating evaluation. Identity equality is therefore undefined
        # until authoritative application. Existing-trajectory actions must
        # retain exact candidate identity.
        if proposed_decision in {"attach", "branch"}:
            same_proposal = (
                same_proposal
                and fresh.get("trajectory_id") == proposed_tid
            )
        if not same_proposal:
            return self.sqlite.resolve_pending_proposal(
                organization_id=self.config.organization_id,
                proposal_id=proposal_id,
                status="stale",
            )
        # Decision persistence has a foreign key to events. Confirmation is
        # an action on the already-persisted advisory event, not a synthetic
        # second ingestion event, so persist the authoritative decision against
        # the original event_id.
        confirm_event_id = row["event_id"]
        result=observe_with_concurrency_recovery(
            self.service,
            service_payload,
            confirm_event_id,
            max_retries=1,
        )
        authoritative_match = result.get("decision") == proposed_decision
        if proposed_decision in {"attach", "branch"}:
            authoritative_match = (
                authoritative_match
                and result.get("trajectory_id") == proposed_tid
            )
        if not authoritative_match:
            raise RuntimeError(
                "authoritative confirmation diverged from revalidated proposal"
            )
        return self.sqlite.resolve_pending_proposal(organization_id=self.config.organization_id, proposal_id=proposal_id, status="confirmed")

    def link_identity(self, *, workspace_id, surface, external_user_id, person_id):
        return self.identities.link(
            workspace_id,
            surface,
            external_user_id,
            person_id,
        )
