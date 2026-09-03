import json,os,tempfile
from collections import Counter
from temperans.platform import TemperansPlatform
from temperans.xyzabc321_dataset import build_xyzabc321
from temperans.xyzabc321_identity import link_xyzabc321_identities
from temperans.frontier_cases_v2 import extract_frontier_v2
from temperans.kimi_frontier_assessor_v2 import KimiFrontierAssessor
key=os.environ.get("MOONSHOT_API_KEY")
if not key:raise SystemExit("Set MOONSHOT_API_KEY")
limit=int(os.environ.get("TEMPERANS_KIMI_MAX_CASES","5"));runs=int(os.environ.get("TEMPERANS_KIMI_RUNS","1"))
with tempfile.TemporaryDirectory() as d:
 p=TemperansPlatform(d);p.create_organization(organization_id="XYZABC321",name="XYZABC321");rt=p.runtime("XYZABC321");link_xyzabc321_identities(rt)
 events,_=build_xyzabc321();cases=extract_frontier_v2(rt,events)[:limit]
 a=KimiFrontierAssessor(key,os.environ.get("TEMPERANS_KIMI_MODEL","kimi-k3"))
 rows=[];correct=wrong=abstain=0
 for i,c in enumerate(cases,1):
  print(f"Kimi frontier V2: {i}/{len(cases)}",flush=True);preds=[];usage=[]
  for _ in range(runs):
   x,u=a.assess(c["event"],c["candidate_views"]);preds.append((x.action,x.candidate_id));usage.append(u)
  pred=Counter(preds).most_common(1)[0][0]
  gold=(c["gold_action"],c["gold_candidate_id"])
  ok=pred==gold
  if pred[0]=="abstain":abstain+=1
  elif ok:correct+=1
  else:wrong+=1
  rows.append({"case_id":c["case_id"],"gold":gold,"predictions":preds,"modal":pred,"correct":ok,"usage":usage})
 total=len(cases)
 print(json.dumps({"cases":total,"correct":correct,"wrong":wrong,"abstain":abstain,
 "accuracy":correct/total if total else 0,"false_route_rate":wrong/total if total else 0,
 "rows":rows},indent=2))
