"""SQLite decision/correction persistence adapter for PilotService."""
from __future__ import annotations

class SQLitePilotAuditStore:
    def __init__(self, sqlite_store, organization_id):
        self.sqlite = sqlite_store
        self.organization_id = organization_id

    def decision(self, row):
        event_id = row["event_id"]
        trace = row.get("trace") or {}
        decision_id = self.sqlite.insert_decision(
            organization_id=self.organization_id,
            event_id=event_id,
            trajectory_id=row.get("trajectory_id"),
            decision=row["decision"],
            trace=trace,
            state_delta=row.get("state_delta") or {},
        )
        return {"record_id": decision_id, **row}

    def correction(self, row):
        correction = row.get("correction") or {
            k: v for k, v in row.items()
            if k not in {"diagnosis", "event_id", "decision_id", "decision_record_id"}
        }
        decision_id = row.get("decision_id") or row.get("decision_record_id")
        correction_id = self.sqlite.insert_correction(
            organization_id=self.organization_id,
            event_id=row.get("event_id"),
            decision_id=decision_id,
            correction=correction,
            diagnosis=row.get("diagnosis"),
        )
        return {"correction_id": correction_id, **row}
