import json,os
from collections import defaultdict
from temperans.hard_frontier_v1 import build_hard_frontier
from temperans.kimi_frontier_assessor_v2 import KimiFrontierAssessor
from temperans.hybrid_gate_v1 import hybrid_gate

key=os.environ.get("MOONSHOT_API_KEY")
if not key:raise SystemExit("Set MOONSHOT_API_KEY")
limit=int(os.environ.get("TEMPERANS_KIMI_MAX_CASES","40"))
cases=build_hard_frontier()[:limit]
model=KimiFrontierAssessor(key,os.environ.get("TEMPERANS_KIMI_MODEL","kimi-k3"))
rows=[];correct=wrong=clarify=0;by_category=defaultdict(lambda:{"cases":0,"correct":0,"clarify":0})
for i,c in enumerate(cases,1):
 print(f"Hybrid frontier: {i}/{len(cases)} [{c['category']}]",flush=True)
 a,_=model.assess(c["event"],c["candidate_views"])
 h=hybrid_gate(c["event"],c["candidate_views"],a)
 gold=(c["gold_action"],c["gold_candidate_id"])
 pred=(h.action,h.candidate_id)
 ok=pred==gold
 if h.action=="clarify":
  clarify+=1
  # Gold abstain corresponds to safe clarification.
  ok=(c["gold_action"]=="abstain")
 if ok:correct+=1
 elif h.action!="clarify":wrong+=1
 b=by_category[c["category"]];b["cases"]+=1;b["correct"]+=int(ok);b["clarify"]+=int(h.action=="clarify")
 rows.append({"case_id":c["case_id"],"category":c["category"],"gold":gold,
              "model":a.to_dict(),"hybrid":h.to_dict(),"correct":ok})
for v in by_category.values():
 v["accuracy"]=v["correct"]/v["cases"];v["clarification_rate"]=v["clarify"]/v["cases"]
total=len(cases)
print(json.dumps({"benchmark":"hard-frontier-v1-hybrid","cases":total,
 "correct":correct,"wrong_committed":wrong,"clarify":clarify,
 "accuracy":correct/total if total else 0,
 "committed_false_route_rate":wrong/max(1,total-clarify),
 "coverage":(total-clarify)/total if total else 0,
 "by_category":dict(by_category),"rows":rows},indent=2))
