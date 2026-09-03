import json,os
from collections import Counter,defaultdict
from temperans.hard_frontier_v1 import build_hard_frontier
from temperans.kimi_frontier_assessor_v2 import KimiFrontierAssessor

key=os.environ.get("MOONSHOT_API_KEY")
if not key: raise SystemExit("Set MOONSHOT_API_KEY")
limit=int(os.environ.get("TEMPERANS_KIMI_MAX_CASES","8"))
runs=int(os.environ.get("TEMPERANS_KIMI_RUNS","1"))
cases=build_hard_frontier()[:limit]
assessor=KimiFrontierAssessor(key,os.environ.get("TEMPERANS_KIMI_MODEL","kimi-k3"))

rows=[];correct=wrong=abstain=0;by_category=defaultdict(lambda:{"cases":0,"correct":0})
by_action=defaultdict(lambda:{"cases":0,"correct":0})
for i,c in enumerate(cases,1):
    print(f"Hard frontier: {i}/{len(cases)} [{c['category']}] gold={c['gold_action']}",flush=True)
    preds=[];usage=[]
    for _ in range(runs):
        x,u=assessor.assess(c["event"],c["candidate_views"])
        preds.append((x.action,x.candidate_id));usage.append(u)
    modal=Counter(preds).most_common(1)[0][0]
    gold=(c["gold_action"],c["gold_candidate_id"])
    ok=modal==gold
    correct+=int(ok)
    if modal[0]=="abstain":abstain+=1
    elif not ok:wrong+=1
    for bucket,keyname in ((by_category,c["category"]),(by_action,c["gold_action"])):
        bucket[keyname]["cases"]+=1;bucket[keyname]["correct"]+=int(ok)
    rows.append({"case_id":c["case_id"],"category":c["category"],"gold":gold,
                 "modal":modal,"correct":ok,"predictions":preds,"usage":usage})
for group in (by_category,by_action):
    for v in group.values():v["accuracy"]=v["correct"]/v["cases"]
total=len(cases)
print(json.dumps({"benchmark":"hard-frontier-v1","model":assessor.model,
 "cases":total,"correct":correct,"wrong":wrong,"predicted_abstain":abstain,
 "accuracy":correct/total if total else 0,"false_route_rate":wrong/total if total else 0,
 "by_action":dict(by_action),"by_category":dict(by_category),"rows":rows},indent=2))
