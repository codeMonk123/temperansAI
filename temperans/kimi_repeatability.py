from collections import defaultdict
from temperans.model_evaluation import evaluate_provider
from temperans.perception_provider import PerceptionRequest
def run_repeated(provider,cases,runs=3):
 out=[]
 for case in cases:
  seen=defaultdict(list)
  for _ in range(runs):
   r=evaluate_provider(provider,PerceptionRequest(event=case["event"],candidate_views=case.get("candidate_views",[])))
   for s in r.signals: seen[s.signal].append(float(s.value))
  out.append({"case_id":case["case_id"],"signals":{k:{"values":v,"range":max(v)-min(v)} for k,v in seen.items()}})
 return out
