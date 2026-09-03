import ast,json
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from temperans.frontier_assessment import FrontierAssessment
class KimiFrontierAssessor:
 def __init__(self,api_key,model="kimi-k3",base_url="https://api.moonshot.ai/v1"):
  self.api_key=api_key;self.model=model;self.base_url=base_url.rstrip("/")
 def _parse(self,s):
  s=(s or "").strip()
  if s.startswith("```"):s="\n".join(s.splitlines()[1:-1]).strip().removeprefix("json").strip()
  try:return json.loads(s)
  except Exception:
   a=s.find("{");b=s.rfind("}");return ast.literal_eval(s[a:b+1])
 def assess(self,event,candidates):
  prompt='Return ONLY {"action":"new|attach|branch|abstain","candidate_id":null or supplied trajectory_id,"confidence":0..1,"evidence":[]}. Choose NEW when this is distinct work. Never invent candidate IDs.\n'+json.dumps({"event":event,"candidates":candidates},sort_keys=True)
  body={"model":self.model,"temperature":1,"messages":[{"role":"system","content":"You route work trajectories conservatively. Structured object only."},{"role":"user","content":prompt}]}
  req=Request(self.base_url+"/chat/completions",data=json.dumps(body).encode(),method="POST",headers={"Authorization":"Bearer "+self.api_key,"Content-Type":"application/json"})
  try:
   with urlopen(req,timeout=90) as r:raw=json.loads(r.read())
  except HTTPError as e:raise RuntimeError(f"Kimi HTTP {e.code}: {e.read().decode(errors='replace')}") from e
  x=self._parse(raw["choices"][0]["message"].get("content",""))
  valid={c["trajectory_id"] for c in candidates};action=x["action"];cid=x.get("candidate_id")
  if cid is not None and cid not in valid:raise ValueError("Kimi invented candidate_id")
  return FrontierAssessment(action,cid,float(x["confidence"]),list(x.get("evidence",[]))),raw.get("usage",{})
