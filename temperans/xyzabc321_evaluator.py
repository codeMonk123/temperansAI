from collections import defaultdict
def _clean(e):
 x=dict(e); x.pop("_gold_trajectory",None); return x
def evaluate(runtime,events):
 predicted=defaultdict(list); gold={}; decisions=defaultdict(int)
 for e in events:
  gold[e["event_id"]]=e["_gold_trajectory"]; r=runtime.observe(_clean(e))
  predicted[r["trajectory_id"]].append(e["event_id"]); decisions[r["decision"]]+=1
 ep={eid:tid for tid,eids in predicted.items() for eid in eids}
 fm=fs=ok=gp=0; ids=list(gold)
 for i,a in enumerate(ids):
  for b in ids[i+1:]:
   sg=gold[a]==gold[b]; sp=ep[a]==ep[b]
   if sg:
    gp+=1
    if sp: ok+=1
    else: fs+=1
   elif sp: fm+=1
 return {"events":len(events),"gold_trajectories":len(set(gold.values())),
 "predicted_trajectories":len(predicted),"trajectory_pair_recall":ok/gp if gp else 1.0,
 "false_merge_pairs":fm,"false_split_pairs":fs,"decisions":dict(decisions)}
