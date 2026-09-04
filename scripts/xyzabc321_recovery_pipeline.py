#!/usr/bin/env python3
"""XYZABC321 persistent semantic-recovery pipeline: prepare | fill | status.
Development benchmark only. Never accesses XYZABC324.
"""
import argparse,json,os,tempfile
from pathlib import Path
from temperans.platform import TemperansPlatform
from temperans.xyzabc321_dataset import build_xyzabc321
from temperans.xyzabc321_identity import link_xyzabc321_identities
from temperans.workstate import ConversationState
from temperans.sqlite_store import SQLiteStore
from temperans.adjudication_cache import AdjudicationCache,recovery_case_id
from temperans.recovery_case_store import RecoveryCaseStore
from temperans.cached_consensus import cached_new_consensus
from temperans.kimi_frontier_assessor_v2 import KimiFrontierAssessor
from temperans.gemini_frontier_assessor import GeminiFrontierAssessor

DB=Path(os.environ.get("TEMPERANS_ADJUDICATION_DB",".temperans/xyzabc321_full_adjudication.db"))
ORG="XYZABC321"
def clean(e):x=dict(e);x.pop("_gold_trajectory",None);return x
def stores():
 s=SQLiteStore(DB);return s,RecoveryCaseStore(s),AdjudicationCache(s)

def prepare():
 s,cases,cache=stores()
 if cases.rows(ORG):
  print(json.dumps({"status":"already_prepared","cases":len(cases.rows(ORG)),"db":str(DB)},indent=2));return
 with tempfile.TemporaryDirectory() as d:
  p=TemperansPlatform(d);p.create_organization(organization_id=ORG,name=ORG)
  rt=p.runtime(ORG);link_xyzabc321_identities(rt);events,_=build_xyzabc321();R=rt.service.runtime
  seen_gold=set();ordinal=0
  for e in events:
   expected="attach" if e["_gold_trajectory"] in seen_gold else "new"
   ev=rt.adapter.normalize(organization_id=ORG,payload=clean(e))
   person=rt.identities.resolve(ev.workspace_id,ev.surface,ev.external_user_id,True)
   work=rt.extractor.extract(text=ev.text,supplied_goal=ev.goal,entities=ev.entities,artifacts=ev.artifacts)
   c=ConversationState(workspace_id=ev.workspace_id,person_id=person,conversation_id=ev.conversation_id,
    surface=ev.surface,goal=work.goal,current_problem=work.current_problem,entities=work.entities,
    artifacts=work.artifacts,anchors=work.anchors)
   R._anchors(c);cand=[t for t in R.trajectories.values() if t.workspace_id==c.workspace_id and t.person_id==c.person_id]
   r=rt.observe(clean(e))
   if r["decision"]=="new":seen_gold.add(e["_gold_trajectory"])
   if r["decision"]!="clarify" or len(cand)!=1:continue
   t=cand[0];score=float(R.semantic_scorer(t,c));lang=R.language.extract(candidate_text=R._text(t),new_text=R._text(c))
   ld=R.linker.decide(trajectory=t,conversation=c,semantic_score=score,
    branch_signal=lang.has_branch_signal,continuation_signal=lang.has_continuation_signal)
   if R.anchor_recall.relevant(t,c) or ld.decision!="uncertain":continue
   view=t.to_dict();view["anchors"]=[a.to_dict() for a in t.anchors]
   event=clean(e);cid=recovery_case_id(event,[view]);ordinal+=1
   cases.put(ORG,cid,e["event_id"],ordinal,event,[view],expected,e["_gold_trajectory"])
 print(json.dumps({"status":"prepared","cases":len(cases.rows(ORG)),"db":str(DB)},indent=2))

def fill():
 s,cases,cache=stores();rows=cases.rows(ORG)
 if not rows:raise SystemExit("Run prepare first")
 k=os.environ.get("MOONSHOT_API_KEY");g=os.environ.get("GEMINI_API_KEY")
 kp=KimiFrontierAssessor(k,os.environ.get("TEMPERANS_KIMI_MODEL","kimi-k3")) if k else None
 gp=GeminiFrontierAssessor(g,os.environ.get("TEMPERANS_GEMINI_MODEL","gemini-3.6-flash")) if g else None
 budget=int(os.environ.get("TEMPERANS_BATCH_MAX_CALLS","20"));calls=success=0
 for row in rows:
  for role,provider,model in (("primary",kp,os.environ.get("TEMPERANS_KIMI_MODEL","kimi-k3")),
                              ("verifier",gp,os.environ.get("TEMPERANS_GEMINI_MODEL","gemini-3.6-flash"))):
   if calls>=budget:break
   if cache.get(ORG,row["case_id"],role) is not None or provider is None:continue
   calls+=1;print(f"Fill {calls}/{budget} {role}: {row['event_id']}",flush=True)
   try:
    a,_=provider.assess(row["event"],row["candidates"])
    cache.put(ORG,row["case_id"],role,model,a.to_dict());success+=1
   except Exception as ex:
    print("  pending:",type(ex).__name__,str(ex)[:120],flush=True)
  if calls>=budget:break
 status(calls=calls,success=success)

def status(calls=0,success=0):
 s,cases,cache=stores();rows=cases.rows(ORG);pc=vc=acc=0;reasons={}
 for row in rows:
  p,v=cache.pair(ORG,row["case_id"]);pc+=p is not None;vc+=v is not None
  d=cached_new_consensus(p,v);acc+=d["accepted"];reasons[d["reason"]]=reasons.get(d["reason"],0)+1
 print(json.dumps({"db":str(DB),"cases":len(rows),"primary_cached":pc,"verifier_cached":vc,
  "consensus_new":acc,"pending_primary":len(rows)-pc,"pending_verifier":len(rows)-vc,
  "calls_this_run":calls,"successful_writes_this_run":success,"reasons":reasons,"zero_api_status":True},indent=2))

if __name__=="__main__":
 a=argparse.ArgumentParser();a.add_argument("command",choices=["prepare","fill","status"]);x=a.parse_args()
 {"prepare":prepare,"fill":fill,"status":status}[x.command]()
