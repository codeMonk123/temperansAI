from pathlib import Path

from temperans.pilot_store import PilotStore
from temperans.redaction import Redactor
from temperans.runtime_v2 import TemperansRuntimeV2
from temperans.pilot_snapshot import TrajectorySnapshotStore
from temperans.workstate import ConversationState


class PilotService:
    def __init__(self, root=".temperans/pilot", audit_store=None):
        self.root = Path(root)
        # PilotStore remains temporarily for event compatibility only.
        # Decisions/corrections use audit_store when supplied.
        self.store = PilotStore(self.root)
        self.audit_store = audit_store
        self.redactor = Redactor()
        self.runtime = TemperansRuntimeV2(
            semantic_scorer=self.score,
            candidate_floor=.12,
        )
        self.snapshots = TrajectorySnapshotStore(
            self.root / "trajectories.json"
        )
        self.runtime.trajectories.update(self.snapshots.load())

    @staticmethod
    def score(t, c):
        a = set((t.durable_goal + " " + t.current_state).lower().split())
        b = set((c.goal + " " + c.current_problem).lower().split())
        return len(a & b) / len(a | b) if a and b else 0.0

    def observe(self, data, event_id=None):
        r = self.redactor.redact(data["current_problem"])
        person_id = data.get("person_id")
        if not person_id:
            raise ValueError(
                "person_id is required; identity resolution belongs to OrganizationRuntime"
            )

        state = ConversationState(
            workspace_id=data["workspace_id"],
            person_id=person_id,
            conversation_id=data["conversation_id"],
            surface=data["surface"],
            goal=data.get("goal", ""),
            current_problem=r.text,
            entities=data.get("entities", []),
            artifacts=data.get("artifacts", []),
            decisions=data.get("decisions", []),
            outcomes=data.get("outcomes", []),
            unresolved=data.get("unresolved", []),
        )

        # Keep legacy event JSONL only until the event compatibility surface is
        # removed. SQLite is already authoritative for canonical ingestion.
        ev = self.store.event({
            **data,
            "current_problem": r.text,
            "redacted": r.redacted,
            "redaction_categories": r.categories,
        })

        result = self.runtime.process(state)
        self.snapshots.save(self.runtime.trajectories)

        decision_row = {
            "event_id": event_id,
            "event_record_id": ev["record_id"],
            **result.to_dict(),
            # Real contemporaneous delta is added in trajectory migration.
            "state_delta": {},
        }

        if self.audit_store is not None:
            if not event_id:
                raise ValueError("event_id is required for SQLite decision persistence")
            dr = self.audit_store.decision(decision_row)
        else:
            dr = self.store.decision(decision_row)

        options = []
        if result.decision == "clarify":
            options = [
                {
                    "action": "attach",
                    "trajectory_id": t.trajectory_id,
                    "label": t.durable_goal or t.current_state,
                }
                for t in self.runtime.trajectories.values()
                if t.workspace_id == state.workspace_id
                and t.person_id == state.person_id
            ][:5]
            options += [
                {"action": "new", "trajectory_id": None, "label": "Start new work"},
                {
                    "action": "branch",
                    "trajectory_id": result.trajectory_id,
                    "label": "Related, but separate branch",
                },
            ]

        return {
            **result.to_dict(),
            "decision_record_id": dr["record_id"],
            "clarification_options": options,
        }

    def link_identity(self, data):
        raise RuntimeError("identity linking moved to OrganizationRuntime")

    def correct(self, data):
        allowed = {"confirm", "attach", "new", "branch", "split", "merge"}
        action = data.get("action")
        if action not in allowed:
            raise ValueError("unsupported correction")

        if self.audit_store is not None:
            structured = {
                "event_id": data.get("event_id"),
                "decision_id": data.get("decision_id") or data.get("decision_record_id"),
                "correction": {
                    "source": data.get("source", "user"),
                    "decision": action,
                    "trajectory_id": data.get("trajectory_id"),
                    "reason_code": data.get("reason_code"),
                    "raw": data,
                },
                "diagnosis": data.get("diagnosis"),
            }
            return self.audit_store.correction(structured)

        return self.store.correction(data)

    def corrections(self):
        if self.audit_store is not None:
            rows = self.audit_store.sqlite.conn.execute(
                """
                SELECT correction_id, event_id, decision_id,
                       correction_json, diagnosis_json, created_at
                FROM corrections
                WHERE organization_id=?
                ORDER BY created_at, correction_id
                """,
                (self.audit_store.organization_id,),
            ).fetchall()
            import json
            return [
                {
                    "correction_id": row["correction_id"],
                    "event_id": row["event_id"],
                    "decision_id": row["decision_id"],
                    "correction": json.loads(row["correction_json"]),
                    "diagnosis": (
                        json.loads(row["diagnosis_json"])
                        if row["diagnosis_json"] else None
                    ),
                    "recorded_at": row["created_at"],
                }
                for row in rows
            ]
        return self.store.read("corrections.jsonl")

    def trajectory(self, trajectory_id):
        t = self.runtime.trajectories.get(trajectory_id)
        if t is None:
            return None
        x = t.to_dict()
        x["anchors"] = [a.to_dict() for a in t.anchors]
        x["context_pack"] = self.runtime.context.build(t).to_dict()
        return x

    def trajectories(self, workspace_id, person_id):
        return [
            {
                "trajectory_id": t.trajectory_id,
                "goal": t.durable_goal,
                "current_state": t.current_state,
                "lifecycle": t.lifecycle,
                "surfaces": t.surfaces,
                "conversation_ids": t.conversation_ids,
            }
            for t in self.runtime.trajectories.values()
            if t.workspace_id == workspace_id and t.person_id == person_id
        ]
