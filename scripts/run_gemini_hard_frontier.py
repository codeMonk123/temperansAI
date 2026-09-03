import json,os
from collections import defaultdict
from temperans.hard_frontier_v1 import build_hard_frontier
from temperans.gemini_frontier_assessor import GeminiFrontierAssessor
key=os.environ.get("GEMINI_API_KEY")
if not key:raise SystemExit("Set GEMINI_API_KEY")
limit=int(os.environ.get("TEMPERANS_GEMINI_MAX_CASES","5"))
cases=build_hard_frontier()[:limit];a=GeminiFrontierAssessor(key)
rows=[];correct=wrong=abstain=0;by=defaultdict(lambda:{"cases":0,"correct":0})
for i,c in enumerate(cases,1):
 print(f"Gemini frontier: {i}/{len(cases)} [{c['category']}]",flush=True)
 x,u=a.assess(c["event"],c["candidate_views"]);pred=(x.action,x.candidate_id);gold=(c["gold_action"],c["gold_candidate_id"]);ok=pred==gold
 correct+=int(ok);wrong+=int(not ok and pred[0]!="abstain");abstain+=int(pred[0]=="abstain")
 b=by[c["category"]];b["cases"]+=1;b["correct"]+=int(ok)
 rows.append({"case_id":c["case_id"],"category":c["category"],"gold":gold,"prediction":pred,"correct":ok,"confidence":x.confidence,"usage":u})
for v in by.values():v["accuracy"]=v["correct"]/v["cases"]
total=len(cases)
print(json.dumps({"benchmark":"hard-frontier-v1","provider":"gemini","model":a.model,"cases":total,
 "correct":correct,"wrong":wrong,"predicted_abstain":abstain,"accuracy":correct/total if total else 0,
 "false_route_rate":wrong/total if total else 0,"by_category":dict(by),"rows":rows},indent=2))
