from collections import Counter
def choose(assessments,min_same=.5):
 if not assessments:return None
 best=max(assessments,key=lambda x:x.same_work)
 return best.candidate_id if best.same_work>=min_same else None
def evaluate_runs(cases,assessor,runs=3):
 rows=[];correct=wrong=abstain=0
 for c in cases:
  picks=[];usages=[]
  for _ in range(runs):
   a,u=assessor.assess(c["event"],c["candidate_views"]);picks.append(choose(a));usages.append(u)
  modal=Counter(picks).most_common(1)[0][0]
  # Synthetic gold IDs are not generated trajectory IDs. Correctness is
  # evaluated using ticket-anchor correspondence in candidate views/event text.
  event_text=str((c["event"].get("content") or {}).get("text",""))
  gold_pick=None
  for v in c["candidate_views"]:
   if any(tok in event_text for tok in str(v.get("goal","")).split() if "-" in tok):
    gold_pick=v["trajectory_id"];break
  if modal is None:abstain+=1
  elif modal==gold_pick:correct+=1
  else:wrong+=1
  rows.append({"case_id":c["case_id"],"picks":picks,"modal_pick":modal,"gold_pick":gold_pick,
   "stable":len(set(picks))==1,"usage":usages})
 total=len(cases)
 return {"cases":total,"correct":correct,"wrong":wrong,"abstain":abstain,
  "accuracy_on_all":correct/total if total else 0,
  "additional_coverage":(correct+wrong)/total if total else 0,
  "false_route_rate":wrong/total if total else 0,
  "stable_rate":sum(r["stable"] for r in rows)/total if total else 0,"rows":rows}
