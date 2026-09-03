import json,os,tempfile
from temperans.platform import TemperansPlatform
from temperans.xyzabc321_dataset import build_xyzabc321
from temperans.xyzabc321_identity import link_xyzabc321_identities
from temperans.kimi_frontier_assessor_v2 import KimiFrontierAssessor
from temperans.gemini_frontier_assessor import GeminiFrontierAssessor
from temperans.provider_resilience import ResilientFrontierProvider
from temperans.hybrid_gate_v1 import hybrid_gate
from temperans.hybrid_replay_v1 import replay_hybrid,summarize
providers=[]
if os.environ.get("MOONSHOT_API_KEY"):providers.append(("kimi",KimiFrontierAssessor(os.environ["MOONSHOT_API_KEY"],os.environ.get("TEMPERANS_KIMI_MODEL","kimi-k3"))))
if os.environ.get("GEMINI_API_KEY"):providers.append(("gemini",GeminiFrontierAssessor(os.environ["GEMINI_API_KEY"],os.environ.get("TEMPERANS_GEMINI_MODEL","gemini-3.6-flash"))))
if not providers:raise SystemExit("Set a provider key")
fp=ResilientFrontierProvider(providers,max_retries=0)
with tempfile.TemporaryDirectory() as d:
 p=TemperansPlatform(d);p.create_organization(organization_id="XYZABC321",name="XYZABC321")
 rt=p.runtime("XYZABC321");link_xyzabc321_identities(rt)
 events,_=build_xyzabc321()
 rows=replay_hybrid(rt,events,fp,hybrid_gate)
 report=summarize(rows);report["rows"]=rows
 open("xyzabc321_hybrid_replay_v1.json","w").write(json.dumps(report,indent=2))
 print(json.dumps({k:v for k,v in report.items() if k!="rows"},indent=2))
