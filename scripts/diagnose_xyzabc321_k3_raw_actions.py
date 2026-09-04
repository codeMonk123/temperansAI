#!/usr/bin/env python3
"""XYZABC321 raw K3 action diagnostic. Development-only. No mutation recovery, no XYZABC324."""
import json,os,tempfile
from collections import Counter,defaultdict
from temperans.platform import TemperansPlatform
from temperans.xyzabc321_dataset import build_xyzabc321
from temperans.xyzabc321_identity import link_xyzabc321_identities
from temperans.kimi_frontier_assessor_v2 import KimiFrontierAssessor
from temperans.workstate import ConversationState

def clean(e):
 x=dict(e);x.pop("_gold_trajectory",None);return x

key=os.environ.get("MOONSHOT_API_KEY")
if not key:raise SystemExit("MOONSHOT_API_KEY required")
model=KimiFrontierAssessor(key,os.environ.get("TEMPERANS_KIMI_MODEL","kimi-k3"))
limit=int(os.environ.get("TEMPERANS_RAW_ACTION_MAX_CASES","20"))

with tempfile.TemporaryDirectory() as d:
 p=TemperansPlatform(d);p.create_organization(organization_id="XYZABC321",name="XYZABC321")
 rt=p.runtime("XYZABC321");link_xyzabc321_identities(rt);events,_=build_xyzabc321();R=rt.service.runtime
 seen_gold=set();rows=[]
 for e in events:
  expected="attach" if e["_gold_trajectory"] in seen_gold else "new"
  ev=rt.adapter.normalize(organization_id="XYZABC321",payload=clean(e))
  person=rt.identities.resolve(ev.workspace_id,ev.surface,ev.external_user_id,True)
  work=rt.extractor.extract(text=ev.text,supplied_goal=ev.goal,entities=ev.entities,artifacts=ev.artifacts)
  c=ConversationState(workspace_id=ev.workspace_id,person_id=person,conversation_id=ev.conversation_id,
   surface=ev.surface,goal=work.goal,current_problem=work.current_problem,
   entities=work.entities,artifacts=work.artifacts,anchors=work.anchors)
  R._anchors(c)
  candidates=[t for t in R.trajectories.values() if t.workspace_id==c.workspace_id and t.person_id==c.person_id]
  result=rt.observe(clean(e))
  if result["decision"]!="clarify":
   if result["decision"]=="new":seen_gold.add(e["_gold_trajectory"])
   continue
  if len(rows)>=limit:continue
  views=[]
  for t in candidates:
   v=t.to_dict();v["anchors"]=[a.to_dict() for a in t.anchors];views.append(v)
  print(f"Raw K3 {len(rows)+1}/{limit}: {e['event_id']} expected={expected}",flush=True)
  try:
   a,u=model.assess(clean(e),views)
   pred=a.action;cid=a.candidate_id;conf=a.confidence
  except Exception as ex:
   pred="provider_error";cid=None;conf=None;u={"error":str(ex)}
  rows.append({"event_id":e["event_id"],"gold_work":e["_gold_trajectory"],
   "expected_action":expected,"k3_action":pred,"k3_candidate_id":cid,
   "k3_confidence":conf,"candidate_count":len(views),"usage":u})

 matrix=Counter((r["expected_action"],r["k3_action"]) for r in rows)
 expected_counts=Counter(r["expected_action"] for r in rows)
 action_counts=Counter(r["k3_action"] for r in rows)
 correct=sum(r["expected_action"]==r["k3_action"] for r in rows)
 report={"development_set":"XYZABC321","model":os.environ.get("TEMPERANS_KIMI_MODEL","kimi-k3"),
  "cases":len(rows),"expected_action_counts":dict(expected_counts),
  "k3_action_counts":dict(action_counts),
  "matrix":{f"{a}->{b}":n for (a,b),n in matrix.items()},
  "raw_action_accuracy":correct/len(rows) if rows else 0,"rows":rows}
 open("xyzabc321_k3_raw_actions.json","w").write(json.dumps(report,indent=2))
 print(json.dumps({k:v for k,v in report.items() if k!="rows"},indent=2))
