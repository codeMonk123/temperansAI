"""XYZABC321 Hybrid V1 evaluation.
Deterministic commits are preserved. Deterministic clarifications are evaluated
through resilient L2 provider + Hybrid Gate, without mutating the benchmark runtime.
"""
from collections import defaultdict
from temperans.provider_resilience import ResilientFrontierProvider
from temperans.hybrid_gate_v1 import hybrid_gate

def _clean(e):
 x=dict(e); x.pop("_gold_trajectory",None); return x

def evaluate_hybrid(runtime,events,frontier_provider):
 gold_runtime={}
 metrics=defaultdict(int); rows=[]
 for e in events:
  clean=_clean(e); gold=e["_gold_trajectory"]
  person=runtime.identities.resolve(clean["workspace_id"],clean["surface"],
                                    clean["external_user_id"],True)
  candidates=[]
  for t in runtime.service.runtime.trajectories.values():
   if t.workspace_id==clean["workspace_id"] and t.person_id==person:
    x=t.to_dict(); x["anchors"]=[a.to_dict() for a in t.anchors]; candidates.append(x)
  result=runtime.observe(clean)
  expected_id=gold_runtime.get(gold)
  expected=("attach",expected_id) if expected_id else ("new",None)

  if result["decision"]!="clarify":
   pred=(result["decision"],result.get("trajectory_id"))
   # generated IDs are learned when the first correct NEW/BRANCH commits.
   if expected[0]=="new" and result["decision"]=="new":
    gold_runtime[gold]=result["trajectory_id"]; expected=("new",None); pred=("new",None)
   elif expected[0]=="attach" and result["decision"]=="attach":
    pred=("attach",result.get("trajectory_id"))
   ok=pred==expected
   metrics["deterministic_committed"]+=1
   metrics["correct"]+=int(ok); metrics["wrong_committed"]+=int(not ok)
   rows.append({"event_id":e["event_id"],"source":"deterministic","gold":expected,"pred":pred,"correct":ok})
   continue

  rr,_=frontier_provider.assess(clean,candidates)
  if rr.unavailable or rr.assessment is None:
   metrics["clarify"]+=1
   rows.append({"event_id":e["event_id"],"source":"provider_unavailable","gold":expected,"pred":("clarify",None),"correct":False})
   continue
  gate=hybrid_gate(clean,candidates,rr.assessment)
  pred=(gate.action,gate.candidate_id)
  if gate.action=="clarify":
   metrics["clarify"]+=1
   rows.append({"event_id":e["event_id"],"source":rr.provider,"gold":expected,"pred":pred,"correct":False})
   continue
  ok=pred==expected
  if expected[0]=="new" and gate.action=="new":
   # Counterfactual evaluation cannot create the proposed trajectory in the
   # already-processed runtime, so record safe NEW coverage only.
   pred=("new",None);ok=True
  metrics["model_committed"]+=1;metrics["correct"]+=int(ok);metrics["wrong_committed"]+=int(not ok)
  rows.append({"event_id":e["event_id"],"source":rr.provider,"gold":expected,"pred":pred,"correct":ok})

 total=len(events);committed=metrics["deterministic_committed"]+metrics["model_committed"]
 return {"events":total,"deterministic_committed":metrics["deterministic_committed"],
 "model_committed":metrics["model_committed"],"committed":committed,
 "coverage":committed/total if total else 0,"clarify":metrics["clarify"],
 "correct":metrics["correct"],"wrong_committed":metrics["wrong_committed"],
 "committed_accuracy":metrics["correct"]/committed if committed else 0,
 "committed_false_route_rate":metrics["wrong_committed"]/committed if committed else 0,
 "rows":rows}
