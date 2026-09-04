#!/usr/bin/env python3
"""Incrementally fill persistent K3/Gemini adjudications. Successful work is never lost."""
import os,json,tempfile
from pathlib import Path
from temperans.sqlite_store import SQLiteStore
from temperans.adjudication_cache import AdjudicationCache,recovery_case_id
from temperans.recovery_case_store import RecoveryCaseStore
from temperans.kimi_frontier_assessor_v2 import KimiFrontierAssessor
from temperans.gemini_frontier_assessor import GeminiFrontierAssessor

DB=Path(os.environ.get("TEMPERANS_ADJUDICATION_DB",".temperans/xyzabc321_adjudication.db"))
s=SQLiteStore(DB);cache=AdjudicationCache(s);cases=RecoveryCaseStore(s)
# Import cases from prior raw diagnostic rows when present. These are development-only.
raw=Path("xyzabc321_k3_raw_actions.json")
if not raw.exists():raise SystemExit("xyzabc321_k3_raw_actions.json missing; keep/generate development diagnostic artifact")
data=json.loads(raw.read_text())
for i,r in enumerate(data["rows"]):
 event={"event_id":r["event_id"],"_gold_work":r["gold_work"]}
 candidates=[{"trajectory_id":r.get("k3_candidate_id") or "development_candidate"}]
 cid=recovery_case_id(event,candidates)
 cases.put("XYZABC321",cid,r["event_id"],i,event,candidates,r["expected_action"],r["gold_work"])

k=os.environ.get("MOONSHOT_API_KEY");g=os.environ.get("GEMINI_API_KEY")
kp=KimiFrontierAssessor(k,os.environ.get("TEMPERANS_KIMI_MODEL","kimi-k3")) if k else None
gp=GeminiFrontierAssessor(g,os.environ.get("TEMPERANS_GEMINI_MODEL","gemini-3.6-flash")) if g else None
budget=int(os.environ.get("TEMPERANS_BATCH_MAX_CALLS","20"));calls=0
for row in cases.rows("XYZABC321"):
 if calls>=budget:break
 cid=row["case_id"]
 # Cache already-known K3 result from raw diagnostic if available.
 original=next((x for x in data["rows"] if x["event_id"]==row["event_id"]),None)
 if cache.get("XYZABC321",cid,"primary") is None and original:
  cache.put("XYZABC321",cid,"primary",data.get("model","kimi-k3"),
   {"action":original["k3_action"],"candidate_id":original.get("k3_candidate_id"),
    "confidence":original.get("k3_confidence") or 0.0,"evidence":[],"maturity":"L2"})
 # The old raw artifact lacks full event/candidate snapshots, so verifier calls are unsafe.
 # Leave verifier pending rather than fabricate context.
status=[]
for row in cases.rows("XYZABC321"):
 p,v=cache.pair("XYZABC321",row["case_id"])
 status.append({"case_id":row["case_id"],"event_id":row["event_id"],
  "primary_cached":p is not None,"verifier_cached":v is not None})
print(json.dumps({"db":str(DB),"cases":len(status),
 "primary_cached":sum(x["primary_cached"] for x in status),
 "verifier_cached":sum(x["verifier_cached"] for x in status),
 "pending_verifier":sum(not x["verifier_cached"] for x in status),
 "note":"No unsafe verifier calls made from incomplete historical snapshots."},indent=2))
