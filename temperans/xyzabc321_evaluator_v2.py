"""Abstention-aware trajectory evaluator."""
from collections import defaultdict
def _clean(e):
 x=dict(e);x.pop("_gold_trajectory",None);return x
def evaluate_v2(runtime,events):
 committed={};gold={};decisions=defaultdict(int);abstained=[]
 for e in events:
  gold[e["event_id"]]=e["_gold_trajectory"];r=runtime.observe(_clean(e));decisions[r["decision"]]+=1
  if r["decision"]=="clarify":abstained.append(e["event_id"]);continue
  committed[e["event_id"]]=r["trajectory_id"]
 ids=list(committed);fm=fs=tp=0
 for i,a in enumerate(ids):
  for b in ids[i+1:]:
   sg=gold[a]==gold[b];sp=committed[a]==committed[b]
   if sg and sp:tp+=1
   elif sg and not sp:fs+=1
   elif not sg and sp:fm+=1
 precision=tp/(tp+fm) if tp+fm else 1.0
 recall=tp/(tp+fs) if tp+fs else 0.0
 return {"events":len(events),"gold_trajectories":len(set(gold.values())),
 "committed_events":len(committed),"abstained_events":len(abstained),
 "automatic_coverage":len(committed)/len(events),"clarification_rate":len(abstained)/len(events),
 "committed_pair_precision":precision,"committed_pair_recall":recall,
 "committed_false_merge_pairs":fm,"committed_false_split_pairs":fs,
 "decisions":dict(decisions)}
