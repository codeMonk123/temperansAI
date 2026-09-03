import json,os,tempfile
from temperans.platform import TemperansPlatform
from temperans.xyzabc321_dataset import build_xyzabc321
from temperans.xyzabc321_identity import link_xyzabc321_identities
from temperans.frontier_cases import extract_frontier
from temperans.kimi_candidate_assessor import KimiCandidateAssessor
from temperans.frontier_scoring import choose

key=os.environ.get("MOONSHOT_API_KEY")
if not key: raise SystemExit("Set MOONSHOT_API_KEY first")

runs=int(os.environ.get("TEMPERANS_KIMI_RUNS","1"))
max_cases=int(os.environ.get("TEMPERANS_KIMI_MAX_CASES","5"))
model=os.environ.get("TEMPERANS_KIMI_MODEL","kimi-k3")

with tempfile.TemporaryDirectory() as d:
 p=TemperansPlatform(d);p.create_organization(organization_id="XYZABC321",name="XYZABC321")
 rt=p.runtime("XYZABC321");link_xyzabc321_identities(rt)
 events,_=build_xyzabc321();cases=extract_frontier(rt,events)[:max_cases]
 assessor=KimiCandidateAssessor(key,model=model)

 rows=[];correct=wrong=abstain=stable=0
 for idx,c in enumerate(cases,1):
  print(f"Kimi frontier: {idx}/{len(cases)}",flush=True)
  picks=[];usages=[]
  for run in range(runs):
   assessments,usage=assessor.assess(c["event"],c["candidate_views"])
   picks.append(choose(assessments));usages.append(usage)

  event_text=str((c["event"].get("content") or {}).get("text",""))
  gold_pick=None
  for v in c["candidate_views"]:
   tokens=[tok for tok in str(v.get("goal","")).split() if "-" in tok]
   if any(tok in event_text for tok in tokens):
    gold_pick=v["trajectory_id"];break

  from collections import Counter
  modal=Counter(picks).most_common(1)[0][0] if picks else None
  is_stable=len(set(picks))==1
  stable+=int(is_stable)
  if modal is None:abstain+=1
  elif modal==gold_pick:correct+=1
  else:wrong+=1
  rows.append({"case_id":c["case_id"],"picks":picks,"modal_pick":modal,
               "gold_pick":gold_pick,"stable":is_stable,"usage":usages})

 total=len(cases)
 report={"model":model,"runs_per_case":runs,"cases":total,"correct":correct,
         "wrong":wrong,"abstain":abstain,
         "accuracy_on_all":correct/total if total else 0,
         "additional_coverage":(correct+wrong)/total if total else 0,
         "false_route_rate":wrong/total if total else 0,
         "stable_rate":stable/total if total else 0,
         "rows":rows}
 print(json.dumps(report,indent=2))
