#!/usr/bin/env python3
"""XYZABC321 DEVELOPMENT run with sequential consensus-NEW recovery."""
import json,os,tempfile
from collections import defaultdict,Counter
from temperans.platform import TemperansPlatform
from temperans.xyzabc321_dataset import build_xyzabc321
from temperans.xyzabc321_identity import link_xyzabc321_identities
from temperans.kimi_frontier_assessor_v2 import KimiFrontierAssessor
from temperans.gemini_frontier_assessor import GeminiFrontierAssessor
from temperans.recovery_runtime import ConsensusNewRecovery
from temperans.retry_provider import RetryProvider
from temperans.workstate import ConversationState

def clean(e):x=dict(e);x.pop("_gold_trajectory",None);return x
k=os.environ.get("MOONSHOT_API_KEY");g=os.environ.get("GEMINI_API_KEY")
if not k or not g:raise SystemExit("Both provider keys required")
rec=ConsensusNewRecovery(KimiFrontierAssessor(k,os.environ.get("TEMPERANS_KIMI_MODEL","kimi-k3")),
 RetryProvider(GeminiFrontierAssessor(g,os.environ.get("TEMPERANS_GEMINI_MODEL","gemini-3.6-flash")),retries=int(os.environ.get("TEMPERANS_GEMINI_RETRIES","2")),backoff=(1,2)))
limit=int(os.environ.get("TEMPERANS_RECOVERY_MAX_CALLS","80"))
with tempfile.TemporaryDirectory() as d:
 p=TemperansPlatform(d);p.create_organization(organization_id="XYZABC321",name="XYZABC321")
 rt=p.runtime("XYZABC321");link_xyzabc321_identities(rt);events,_=build_xyzabc321();R=rt.service.runtime
 gold_tid={};rows=[];calls=0;reasons=Counter()
 for e in events:
  gold=e["_gold_trajectory"];expected="attach" if gold in gold_tid else "new"
  ev=rt.adapter.normalize(organization_id="XYZABC321",payload=clean(e));person=rt.identities.resolve(ev.workspace_id,ev.surface,ev.external_user_id,True)
  work=rt.extractor.extract(text=ev.text,supplied_goal=ev.goal,entities=ev.entities,artifacts=ev.artifacts)
  c=ConversationState(workspace_id=ev.workspace_id,person_id=person,conversation_id=ev.conversation_id,surface=ev.surface,
   goal=work.goal,current_problem=work.current_problem,entities=work.entities,artifacts=work.artifacts,anchors=work.anchors)
  R._anchors(c);cands=[t for t in R.trajectories.values() if t.workspace_id==c.workspace_id and t.person_id==c.person_id]
  r=rt.observe(clean(e));action=r["decision"];tid=r.get("trajectory_id");source="deterministic"
  if action=="clarify" and len(cands)==1 and calls<limit:
   t=cands[0];score=float(R.semantic_scorer(t,c));lang=R.language.extract(candidate_text=R._text(t),new_text=R._text(c))
   ld=R.linker.decide(trajectory=t,conversation=c,semantic_score=score,branch_signal=lang.has_branch_signal,continuation_signal=lang.has_continuation_signal)
   if not R.anchor_recall.relevant(t,c) and ld.decision=="uncertain":
    v=t.to_dict();v["anchors"]=[a.to_dict() for a in t.anchors];calls+=1;print(f"Consensus NEW {calls}: {e['event_id']}",flush=True)
    x=rec.assess(clean(e),[v]);reasons[x["reason"]]+=1
    if x["accepted"]:
     # Apply NEW through isolated direct runtime state for DEVELOPMENT scoring.
     # This is not production authority wiring.
     nr=R._new(c);tid=nr.trajectory_id;action="new";source="consensus_new"
  if expected=="new" and action=="new":gold_tid[gold]=tid;ok=True
  elif expected=="attach" and action=="attach" and tid==gold_tid.get(gold):ok=True
  else:ok=False
  rows.append({"event_id":e["event_id"],"gold":gold,"expected":expected,"action":action,"trajectory_id":tid,"source":source,"correct":ok})
 by=defaultdict(list);pred=defaultdict(set)
 for x in rows:
  by[x["gold"]].append(x)
  if x["action"]!="clarify" and x["trajectory_id"]:pred[x["trajectory_id"]].add(x["gold"])
 good=sum(all(y["correct"] for y in ys) for ys in by.values());fm=sum(len(v)>1 for v in pred.values())
 report={"gold_trajectories":len(by),"correctly_reconstructed":good,"trajectory_reconstruction_rate":good/len(by),
 "false_merges":fm,"consensus_calls":calls,"reasons":dict(reasons),"rows":rows}
 open("xyzabc321_consensus_new_result.json","w").write(json.dumps(report,indent=2))
 print(json.dumps({k:v for k,v in report.items() if k!="rows"},indent=2))
