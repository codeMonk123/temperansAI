import json,os
from collections import Counter
from temperans.xyzabc321_dataset import build_xyzabc321
from temperans.gold_frontier import build_gold_frontier
from temperans.kimi_frontier_assessor_v2 import KimiFrontierAssessor
key=os.environ.get("MOONSHOT_API_KEY")
if not key:raise SystemExit("Set MOONSHOT_API_KEY")
limit=int(os.environ.get("TEMPERANS_KIMI_MAX_CASES","6"));runs=int(os.environ.get("TEMPERANS_KIMI_RUNS","1"))
events,_=build_xyzabc321();cases=build_gold_frontier(events)[:limit]
a=KimiFrontierAssessor(key,os.environ.get("TEMPERANS_KIMI_MODEL","kimi-k3"))
rows=[];correct=wrong=abstain=0;by_kind={}
for i,c in enumerate(cases,1):
 print(f"Gold frontier: {i}/{len(cases)} [{c['kind']}]",flush=True);preds=[];usage=[]
 for _ in range(runs):
  x,u=a.assess(c["event"],c["candidate_views"]);preds.append((x.action,x.candidate_id));usage.append(u)
 pred=Counter(preds).most_common(1)[0][0];gold=(c["gold_action"],c["gold_candidate_id"]);ok=pred==gold
 if pred[0]=="abstain":abstain+=1
 elif ok:correct+=1
 else:wrong+=1
 k=by_kind.setdefault(c["kind"],{"cases":0,"correct":0});k["cases"]+=1;k["correct"]+=int(ok)
 rows.append({"case_id":c["case_id"],"kind":c["kind"],"gold":gold,"modal":pred,"correct":ok,"predictions":preds,"usage":usage})
total=len(cases)
for v in by_kind.values():v["accuracy"]=v["correct"]/v["cases"] if v["cases"] else 0
print(json.dumps({"cases":total,"correct":correct,"wrong":wrong,"abstain":abstain,
 "accuracy":correct/total if total else 0,"false_route_rate":wrong/total if total else 0,
 "by_kind":by_kind,"rows":rows},indent=2))
