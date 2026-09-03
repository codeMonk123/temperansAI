"""SQLite-backed signal observation persistence."""
import json,uuid
from temperans.sqlite_store import utc_now,canonical_json
class SQLiteSignalStore:
 def __init__(self,sqlite,organization_id):
  self.sqlite=sqlite;self.organization_id=organization_id
  self.sqlite.conn.execute("""CREATE TABLE IF NOT EXISTS signal_observations(
   signal_id TEXT PRIMARY KEY,organization_id TEXT NOT NULL,event_id TEXT,
   trajectory_id TEXT,signal TEXT NOT NULL,maturity TEXT NOT NULL,
   observation_json TEXT NOT NULL,created_at TEXT NOT NULL,
   FOREIGN KEY(organization_id) REFERENCES organizations(organization_id) ON DELETE CASCADE)""")
  self.sqlite.conn.commit()
 def persist(self,event_id,trajectory_id,signals):
  ids=[]
  with self.sqlite.conn:
   for s in signals:
    sid="sig_"+uuid.uuid4().hex[:16];ids.append(sid)
    self.sqlite.conn.execute("INSERT INTO signal_observations VALUES(?,?,?,?,?,?,?,?)",
      (sid,self.organization_id,event_id,trajectory_id,s.signal,s.maturity,
       canonical_json(s.to_dict()),utc_now()))
  return ids
 def list(self):
  rows=self.sqlite.conn.execute("SELECT observation_json FROM signal_observations WHERE organization_id=? ORDER BY created_at,signal_id",(self.organization_id,)).fetchall()
  return [json.loads(r["observation_json"]) for r in rows]
