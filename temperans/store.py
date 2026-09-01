import json
import sqlite3

from .events import Event


class TrajectoryStore:

    def __init__(self, path="temperans.db"):
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row

        self._create_tables()
        self._migrate_schema()

    def _create_tables(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            event_id TEXT PRIMARY KEY,
            trajectory_id TEXT NOT NULL,
            user_id TEXT,
            conversation_id TEXT,
            thread_id TEXT,
            goal_id TEXT,
            actor_type TEXT NOT NULL,
            actor_id TEXT,
            text TEXT,
            tool_name TEXT,
            status TEXT,
            metadata TEXT,
            timestamp TEXT
        )
        """)

        self.conn.commit()

    def _migrate_schema(self):
        rows = self.conn.execute(
            "PRAGMA table_info(events)"
        ).fetchall()

        columns = {row["name"] for row in rows}

        if "thread_id" not in columns:
            self.conn.execute(
                "ALTER TABLE events "
                "ADD COLUMN thread_id TEXT"
            )

        if "goal_id" not in columns:
            self.conn.execute(
                "ALTER TABLE events "
                "ADD COLUMN goal_id TEXT"
            )

        self.conn.commit()

    def save_event(
        self,
        trajectory_id,
        user_id,
        event,
    ):
        self.conn.execute("""
        INSERT INTO events (
            event_id,
            trajectory_id,
            user_id,
            conversation_id,
            thread_id,
            goal_id,
            actor_type,
            actor_id,
            text,
            tool_name,
            status,
            metadata,
            timestamp
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event.event_id,
            trajectory_id,
            user_id,
            event.conversation_id,
            event.thread_id,
            event.goal_id,
            event.actor_type,
            event.actor_id,
            event.text,
            event.tool_name,
            event.status,
            json.dumps(event.metadata),
            event.timestamp,
        ))

        self.conn.commit()

    def load_events(self, trajectory_id):
        rows = self.conn.execute("""
        SELECT *
        FROM events
        WHERE trajectory_id = ?
        ORDER BY timestamp, rowid
        """, (trajectory_id,)).fetchall()

        events = []

        for row in rows:
            events.append(
                Event(
                    event_id=row["event_id"],
                    actor_type=row["actor_type"],
                    actor_id=row["actor_id"],
                    text=row["text"] or "",
                    conversation_id=row["conversation_id"],
                    thread_id=row["thread_id"],
                    goal_id=row["goal_id"],
                    tool_name=row["tool_name"],
                    status=row["status"],
                    metadata=json.loads(
                        row["metadata"] or "{}"
                    ),
                    timestamp=row["timestamp"],
                )
            )

        return events

    def trace(
        self,
        user_id=None,
        trajectory_id=None,
        conversation_id=None,
        thread_id=None,
        goal_id=None,
        behavior_model=None,
        thread_resolver=None,
    ):
        from .trace import Trace

        return Trace(
            user_id=user_id,
            trajectory_id=trajectory_id,
            conversation_id=conversation_id,
            thread_id=thread_id,
            goal_id=goal_id,
            store=self,
            behavior_model=behavior_model,
            thread_resolver=thread_resolver,
        )

    def close(self):
        self.conn.close()
