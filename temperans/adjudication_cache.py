"""Stable, provider-independent semantic adjudication cache."""
import hashlib,json
def canonical(v):return json.dumps(v,sort_keys=True,separators=(",",":"),default=str)
def recovery_case_id(event,candidates,prompt_version="semantic-new-v1"):
 payload={"event":event,"candidates":candidates,"prompt_version":prompt_version}
 return "rc_"+hashlib.sha256(canonical(payload).encode()).hexdigest()[:24]

class AdjudicationCache:
 def __init__(self,sqlite):self.sqlite=sqlite;self._migrate()
 def _migrate(self):
  self.sqlite.conn.execute("""CREATE TABLE IF NOT EXISTS recovery_adjudications(
   organization_id TEXT NOT NULL,case_id TEXT NOT NULL,provider TEXT NOT NULL,
   model TEXT NOT NULL,assessment_json TEXT NOT NULL,created_at TEXT NOT NULL,
   PRIMARY KEY(organization_id,case_id,provider))""");self.sqlite.conn.commit()
 def put(self,org,case_id,provider,model,assessment):
  from temperans.sqlite_store import canonical_json,utc_now
  with self.sqlite.conn:self.sqlite.conn.execute(
   """INSERT OR IGNORE INTO recovery_adjudications VALUES(?,?,?,?,?,?)""",
   (org,case_id,provider,model,canonical_json(assessment),utc_now()))
  return self.get(org,case_id,provider)
 def get(self,org,case_id,provider):
  r=self.sqlite.conn.execute("""SELECT * FROM recovery_adjudications
   WHERE organization_id=? AND case_id=? AND provider=?""",(org,case_id,provider)).fetchone()
  if not r:return None
  x=dict(r);x["assessment"]=json.loads(x.pop("assessment_json"));return x
 def pair(self,org,case_id):
  return self.get(org,case_id,"primary"),self.get(org,case_id,"verifier")
