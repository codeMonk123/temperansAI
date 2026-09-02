"""SQLite authoritative storage primitives for Temperans Milestone A."""

from __future__ import annotations
import hashlib, json, secrets, sqlite3, uuid
from datetime import datetime, timezone
from pathlib import Path


class ConcurrentTrajectoryUpdate(RuntimeError):
    pass


class EventConflict(ValueError):
    pass


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def payload_hash(value):
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def hash_api_key(key):
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


class SQLiteStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path), timeout=30)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._migrate()

    def close(self):
        self.conn.close()

    def _migrate(self):
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS organizations(
          organization_id TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          config_json TEXT NOT NULL,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS api_keys(
          key_hash TEXT PRIMARY KEY,
          organization_id TEXT NOT NULL,
          created_at TEXT NOT NULL,
          FOREIGN KEY(organization_id) REFERENCES organizations(organization_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS identities(
          organization_id TEXT NOT NULL,
          workspace_id TEXT NOT NULL,
          surface TEXT NOT NULL,
          external_user_id TEXT NOT NULL,
          person_id TEXT NOT NULL,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          PRIMARY KEY(organization_id,workspace_id,surface,external_user_id),
          FOREIGN KEY(organization_id) REFERENCES organizations(organization_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS events(
          record_id TEXT PRIMARY KEY,
          organization_id TEXT NOT NULL,
          event_id TEXT NOT NULL,
          workspace_id TEXT,
          person_id TEXT,
          external_user_id TEXT,
          conversation_id TEXT,
          surface TEXT,
          event_type TEXT,
          occurred_at TEXT,
          received_at TEXT NOT NULL,
          source_sequence TEXT,
          late_event INTEGER NOT NULL DEFAULT 0,
          payload_hash TEXT NOT NULL,
          payload_json TEXT NOT NULL,
          UNIQUE(organization_id,event_id),
          FOREIGN KEY(organization_id) REFERENCES organizations(organization_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS trajectories(
          organization_id TEXT NOT NULL,
          trajectory_id TEXT NOT NULL,
          workspace_id TEXT NOT NULL,
          person_id TEXT NOT NULL,
          durable_goal TEXT NOT NULL DEFAULT '',
          lifecycle TEXT NOT NULL DEFAULT 'active',
          state_json TEXT NOT NULL,
          trajectory_version INTEGER NOT NULL DEFAULT 1,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          PRIMARY KEY(organization_id,trajectory_id),
          FOREIGN KEY(organization_id) REFERENCES organizations(organization_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS decisions(
          decision_id TEXT PRIMARY KEY,
          organization_id TEXT NOT NULL,
          event_id TEXT NOT NULL,
          trajectory_id TEXT,
          decision TEXT NOT NULL,
          state_delta_json TEXT NOT NULL DEFAULT '{}',
          trace_json TEXT NOT NULL,
          created_at TEXT NOT NULL,
          FOREIGN KEY(organization_id) REFERENCES organizations(organization_id) ON DELETE CASCADE,
          FOREIGN KEY(organization_id,event_id) REFERENCES events(organization_id,event_id)
        );
        CREATE TABLE IF NOT EXISTS corrections(
          correction_id TEXT PRIMARY KEY,
          organization_id TEXT NOT NULL,
          event_id TEXT,
          decision_id TEXT,
          correction_json TEXT NOT NULL,
          diagnosis_json TEXT,
          created_at TEXT NOT NULL,
          FOREIGN KEY(organization_id) REFERENCES organizations(organization_id) ON DELETE CASCADE
        );
        """)
        self.conn.commit()

    def create_organization(self, *, organization_id, name, config):
        key = "tmp_live_" + secrets.token_urlsafe(24)
        now = utc_now()
        with self.conn:
            self.conn.execute("INSERT INTO organizations VALUES(?,?,?,?)",
                              (organization_id, name, canonical_json(config), now))
            self.conn.execute("INSERT INTO api_keys VALUES(?,?,?)",
                              (hash_api_key(key), organization_id, now))
        return {"organization_id": organization_id, "api_key": key}

    def get_organization(self, organization_id):
        row = self.conn.execute(
            "SELECT * FROM organizations WHERE organization_id=?",
            (organization_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "organization_id": row["organization_id"],
            "name": row["name"],
            "config": json.loads(row["config_json"]),
            "created_at": row["created_at"],
        }

    def authenticate(self, api_key):
        if not api_key:
            return None
        row = self.conn.execute("""
          SELECT o.* FROM api_keys k JOIN organizations o
          ON o.organization_id=k.organization_id WHERE k.key_hash=?
        """, (hash_api_key(api_key),)).fetchone()
        if not row:
            return None
        return {"organization_id": row["organization_id"], "name": row["name"],
                "config": json.loads(row["config_json"])}

    def link_identity(self, *, organization_id, workspace_id, surface, external_user_id, person_id):
        old = self.resolve_identity(organization_id=organization_id, workspace_id=workspace_id,
                                    surface=surface, external_user_id=external_user_id)
        if old and old != person_id:
            raise ValueError("identity already linked")
        now = utc_now()
        with self.conn:
            self.conn.execute("""
              INSERT INTO identities VALUES(?,?,?,?,?,?,?)
              ON CONFLICT(organization_id,workspace_id,surface,external_user_id)
              DO UPDATE SET person_id=excluded.person_id,updated_at=excluded.updated_at
            """, (organization_id, workspace_id, surface, external_user_id, person_id, now, now))
        return person_id

    def resolve_identity(self, *, organization_id, workspace_id, surface, external_user_id):
        row = self.conn.execute("""
          SELECT person_id FROM identities WHERE organization_id=? AND workspace_id=?
          AND surface=? AND external_user_id=?
        """, (organization_id, workspace_id, surface, external_user_id)).fetchone()
        return row["person_id"] if row else None

    def insert_event(self, *, organization_id, event_id, payload, workspace_id=None,
                     person_id=None, external_user_id=None, conversation_id=None,
                     surface=None, event_type=None, occurred_at=None,
                     source_sequence=None, late_event=False):
        digest = payload_hash(payload)
        old = self.get_event(organization_id=organization_id, event_id=event_id)
        if old:
            if old["payload_hash"] != digest:
                raise EventConflict("event_id payload conflict")
            return old
        rid, now = "evt_" + uuid.uuid4().hex[:16], utc_now()
        try:
            with self.conn:
                self.conn.execute("""
                  INSERT INTO events VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (rid, organization_id, event_id, workspace_id, person_id,
                      external_user_id, conversation_id, surface, event_type,
                      occurred_at, now, source_sequence, int(late_event),
                      digest, canonical_json(payload)))
        except sqlite3.IntegrityError:
            old = self.get_event(organization_id=organization_id, event_id=event_id)
            if old and old["payload_hash"] == digest:
                return old
            if old:
                raise EventConflict("event_id payload conflict")
            raise
        return self.get_event(organization_id=organization_id, event_id=event_id)

    def get_event(self, *, organization_id, event_id):
        row = self.conn.execute("""
          SELECT * FROM events WHERE organization_id=? AND event_id=?
        """, (organization_id, event_id)).fetchone()
        if not row:
            return None
        x = dict(row)
        x["late_event"] = bool(x["late_event"])
        x["payload"] = json.loads(x.pop("payload_json"))
        return x

    def count_events(self, organization_id):
        return self.conn.execute("SELECT COUNT(*) FROM events WHERE organization_id=?",
                                 (organization_id,)).fetchone()[0]

    def create_trajectory(self, *, organization_id, trajectory_id, workspace_id, person_id, state):
        now = utc_now()
        with self.conn:
            self.conn.execute("""
              INSERT INTO trajectories VALUES(?,?,?,?,?,?,?,1,?,?)
            """, (organization_id, trajectory_id, workspace_id, person_id,
                  state.get("durable_goal",""), state.get("lifecycle","active"),
                  canonical_json(state), now, now))
        return self.get_trajectory(organization_id=organization_id, trajectory_id=trajectory_id)

    def get_trajectory(self, *, organization_id, trajectory_id):
        row = self.conn.execute("""
          SELECT * FROM trajectories WHERE organization_id=? AND trajectory_id=?
        """, (organization_id, trajectory_id)).fetchone()
        if not row:
            return None
        x = dict(row)
        x["state"] = json.loads(x.pop("state_json"))
        return x

    def update_trajectory(self, *, organization_id, trajectory_id, expected_version, state):
        now = utc_now()
        with self.conn:
            cur = self.conn.execute("""
              UPDATE trajectories SET durable_goal=?,lifecycle=?,state_json=?,
              trajectory_version=trajectory_version+1,updated_at=?
              WHERE organization_id=? AND trajectory_id=? AND trajectory_version=?
            """, (state.get("durable_goal",""), state.get("lifecycle","active"),
                  canonical_json(state), now, organization_id, trajectory_id, expected_version))
            if cur.rowcount != 1:
                raise ConcurrentTrajectoryUpdate("stale trajectory version")
        return self.get_trajectory(organization_id=organization_id, trajectory_id=trajectory_id)

    def insert_decision(self, *, organization_id, event_id, trajectory_id, decision,
                        trace, state_delta=None, decision_id=None):
        did = decision_id or "dec_" + uuid.uuid4().hex[:16]
        now = utc_now()
        with self.conn:
            self.conn.execute("""
              INSERT INTO decisions VALUES(?,?,?,?,?,?,?,?)
            """, (did, organization_id, event_id, trajectory_id, decision,
                  canonical_json(state_delta or {}), canonical_json(trace), now))
        return did

    def insert_correction(self, *, organization_id, correction, event_id=None,
                          decision_id=None, diagnosis=None, correction_id=None):
        cid = correction_id or "cor_" + uuid.uuid4().hex[:16]
        now = utc_now()
        with self.conn:
            self.conn.execute("""
              INSERT INTO corrections VALUES(?,?,?,?,?,?,?)
            """, (cid, organization_id, event_id, decision_id,
                  canonical_json(correction),
                  canonical_json(diagnosis) if diagnosis is not None else None, now))
        return cid
