"""Persistent recovery cases + adjudications for reproducible semantic replay."""
import json
from temperans.sqlite_store import canonical_json,utc_now
class RecoveryCaseStore:
 def __init__(self,sqlite):self.s=sqlite;self._migrate()
 def _migrate(self):
  self.s.conn.execute("""CREATE TABLE IF NOT EXISTS recovery_cases(
   organization_id TEXT NOT NULL,case_id TEXT NOT NULL,event_id TEXT NOT NULL,
   ordinal INTEGER NOT NULL,event_json TEXT NOT NULL,candidates_json TEXT NOT NULL,
   expected_action TEXT,gold_work TEXT,created_at TEXT NOT NULL,
   PRIMARY KEY(organization_id,case_id))""");self.s.conn.commit()
 def put(self,org,cid,event_id,ordinal,event,candidates,expected_action=None,gold_work=None):
  with self.s.conn:self.s.conn.execute("""INSERT OR IGNORE INTO recovery_cases
   VALUES(?,?,?,?,?,?,?,?,?)""",(org,cid,event_id,ordinal,canonical_json(event),
   canonical_json(candidates),expected_action,gold_work,utc_now()))
 def rows(self,org):
  rs=self.s.conn.execute("""SELECT * FROM recovery_cases WHERE organization_id=?
   ORDER BY ordinal,case_id""",(org,)).fetchall()
  out=[]
  for r in rs:
   x=dict(r);x["event"]=json.loads(x.pop("event_json"));x["candidates"]=json.loads(x.pop("candidates_json"));out.append(x)
  return out
