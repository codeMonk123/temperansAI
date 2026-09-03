"""Zero-API XYZABC321 human trajectory audit.
No Kimi/Gemini calls. Produces a frozen trajectory-level audit artifact.
"""
import json,hashlib,tempfile
from pathlib import Path
from collections import defaultdict
from temperans.platform import TemperansPlatform
from temperans.xyzabc321_dataset import build_xyzabc321
from temperans.xyzabc321_identity import link_xyzabc321_identities

def clean(e):
 x=dict(e);x.pop("_gold_trajectory",None);return x

with tempfile.TemporaryDirectory() as d:
 p=TemperansPlatform(d);p.create_organization(organization_id="XYZABC321",name="XYZABC321")
 rt=p.runtime("XYZABC321");link_xyzabc321_identities(rt)
 events,_=build_xyzabc321()
 by_pred=defaultdict(list)
 decisions=[]
 for e in events:
  r=rt.observe(clean(e))
  decisions.append({"event_id":e["event_id"],"gold_work":e["_gold_trajectory"],
                    "decision":r["decision"],"trajectory_id":r.get("trajectory_id")})
  if r["decision"]!="clarify" and r.get("trajectory_id"):
   by_pred[r["trajectory_id"]].append(e)

 trajectories=[]
 for tid,evs in sorted(by_pred.items()):
  gold_works=sorted({e["_gold_trajectory"] for e in evs})
  trajectories.append({
   "trajectory_id":tid,
   "event_ids":[e["event_id"] for e in evs],
   "events":[e["content"]["text"] for e in evs],
   "gold_work_ids":gold_works,
   "machine_false_merge_hint":len(gold_works)>1
  })

 # Freeze first 20 predicted trajectories deterministically.
 sample=trajectories[:20]
 canonical=json.dumps(sample,sort_keys=True,separators=(",",":"))
 sha=hashlib.sha256(canonical.encode()).hexdigest()
 audit={"audit_version":"trajectory-human-audit-v1","sample_sha256":sha,
        "sample_size":len(sample),"instructions":{
        "human_correct":"Does this predicted trajectory represent one coherent piece of work?",
        "human_false_merge":"Does it incorrectly combine multiple distinct pieces of work?",
        "acceptance":">=70% human_correct and zero human_false_merge"},
        "rows":[]}
 for i,t in enumerate(sample,1):
  audit["rows"].append({"audit_id":f"audit_{i:03d}",**t,
    "human_correct":None,"human_false_merge":None,"human_notes":""})
 Path("xyzabc321_trajectory_human_audit_v1.json").write_text(json.dumps(audit,indent=2))
 summary={"events":len(events),"predicted_committed_trajectories":len(trajectories),
          "clarifications":sum(x["decision"]=="clarify" for x in decisions),
          "audit_sample_size":len(sample),"audit_sha256":sha,
          "audit_file":"xyzabc321_trajectory_human_audit_v1.json"}
 print(json.dumps(summary,indent=2))
 print("\nAUDIT PREVIEW")
 for r in audit["rows"]:
  print(f"\n{r['audit_id']}  {r['trajectory_id']}")
  for text in r["events"]:print("  -",text)
