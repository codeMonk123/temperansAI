"""Small live resilience smoke test: Kimi primary, Gemini fallback."""
import json,os
from temperans.hard_frontier_v1 import build_hard_frontier
from temperans.kimi_frontier_assessor_v2 import KimiFrontierAssessor
from temperans.gemini_frontier_assessor import GeminiFrontierAssessor
from temperans.provider_resilience import ResilientFrontierProvider

k=os.environ.get("MOONSHOT_API_KEY");g=os.environ.get("GEMINI_API_KEY")
if not k or not g:raise SystemExit("Set MOONSHOT_API_KEY and GEMINI_API_KEY")
provider=ResilientFrontierProvider([
 ("kimi",KimiFrontierAssessor(k,os.environ.get("TEMPERANS_KIMI_MODEL","kimi-k3"))),
 ("gemini",GeminiFrontierAssessor(g,os.environ.get("TEMPERANS_GEMINI_MODEL","gemini-3.6-flash")))
],max_retries=2)
case=build_hard_frontier()[0]
r,u=provider.assess(case["event"],case["candidate_views"])
print(json.dumps({"unavailable":r.unavailable,"provider":r.provider,
 "assessment":r.assessment.to_dict() if r.assessment else None,
 "attempts":[a.__dict__ for a in r.attempts],"usage":u},indent=2))
