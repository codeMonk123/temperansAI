"""Hybrid Replay V1.
Replays XYZABC321 sequentially. Deterministic CLARIFY can be resolved by an L2
provider + Hybrid Gate, and accepted NEW/ATTACH/BRANCH decisions are applied
to runtime state for subsequent events. Intended for validation, not production.
"""
def _clean(e):
 x=dict(e);x.pop("_gold_trajectory",None);return x

def _candidate_views(runtime,clean):
 person=runtime.identities.resolve(clean["workspace_id"],clean["surface"],
                                   clean["external_user_id"],True)
 out=[]
 for t in runtime.service.runtime.trajectories.values():
  if t.workspace_id==clean["workspace_id"] and t.person_id==person:
   x=t.to_dict();x["anchors"]=[a.to_dict() for a in t.anchors];out.append(x)
 return out

def replay_hybrid(runtime,events,provider,gate):
 rows=[];gold_to_runtime={}
 for i,e in enumerate(events,1):
  clean=_clean(e);gold=e["_gold_trajectory"]
  candidates=_candidate_views(runtime,clean)
  r=runtime.observe(clean)
  final_action=r["decision"];final_tid=r.get("trajectory_id");source="deterministic"
  if r["decision"]=="clarify":
   rr,_=provider.assess(clean,candidates)
   if rr.unavailable or rr.assessment is None:
    final_action="clarify";final_tid=None;source="provider_unavailable"
   else:
    h=gate(clean,candidates,rr.assessment);source=rr.provider or "model"
    final_action=h.action;final_tid=h.candidate_id
    # Validation replay applies accepted proposals to in-memory trajectory state.
    # NEW is represented as a synthetic accepted work identity for scoring.
    if final_action=="new":
     final_tid="hybrid_"+gold
    elif final_action=="branch":
     final_tid="hybrid_branch_"+gold
  expected_tid=gold_to_runtime.get(gold)
  expected_action="attach" if expected_tid else "new"
  if final_action in {"new","branch"} and expected_tid is None:
   gold_to_runtime[gold]=final_tid
  correct=(final_action==expected_action and
           (expected_action=="new" or final_tid==expected_tid))
  rows.append({"index":i,"event_id":e["event_id"],"gold_work":gold,
               "expected_action":expected_action,"expected_tid":expected_tid,
               "final_action":final_action,"final_tid":final_tid,
               "source":source,"correct":correct})
 return rows

def summarize(rows):
 total=len(rows);committed=[r for r in rows if r["final_action"]!="clarify"]
 correct=sum(r["correct"] for r in committed)
 # Work-level reconstructed: all events for work committed correctly.
 by={}
 for r in rows:by.setdefault(r["gold_work"],[]).append(r)
 good=sum(all(x["correct"] and x["final_action"]!="clarify" for x in xs) for xs in by.values())
 return {"events":total,"committed_events":len(committed),"event_coverage":len(committed)/total,
         "committed_correct":correct,"committed_accuracy":correct/len(committed) if committed else 0,
         "gold_trajectories":len(by),"correctly_reconstructed_trajectories":good,
         "trajectory_reconstruction_rate":good/len(by) if by else 0,
         "clarifications":total-len(committed)}
