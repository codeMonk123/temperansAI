"""Final XYZABC321 resilient-hybrid runner + audit export."""
import json,os,tempfile
from pathlib import Path
from temperans.platform import TemperansPlatform
from temperans.xyzabc321_dataset import build_xyzabc321
from temperans.xyzabc321_identity import link_xyzabc321_identities
from temperans.kimi_frontier_assessor_v2 import KimiFrontierAssessor
from temperans.gemini_frontier_assessor import GeminiFrontierAssessor
from temperans.provider_resilience import ResilientFrontierProvider
from temperans.xyzabc321_hybrid import evaluate_hybrid
from temperans.human_audit import build_audit_sample

k=os.environ.get("MOONSHOT_API_KEY");g=os.environ.get("GEMINI_API_KEY")
providers=[]
if k:providers.append(("kimi",KimiFrontierAssessor(k,os.environ.get("TEMPERANS_KIMI_MODEL","kimi-k3"))))
if g:providers.append(("gemini",GeminiFrontierAssessor(g,os.environ.get("TEMPERANS_GEMINI_MODEL","gemini-3.6-flash"))))
if not providers:raise SystemExit("Set at least one frontier provider API key")
fp=ResilientFrontierProvider(providers,max_retries=1)
with tempfile.TemporaryDirectory() as d:
 p=TemperansPlatform(d);p.create_organization(organization_id="XYZABC321",name="XYZABC321")
 rt=p.runtime("XYZABC321");link_xyzabc321_identities(rt)
 events,_=build_xyzabc321()
 report=evaluate_hybrid(rt,events,fp)
 Path("xyzabc321_hybrid_report.json").write_text(json.dumps(report,indent=2))
 audit=build_audit_sample(report["rows"],n=20)
 Path("xyzabc321_human_audit_v1.json").write_text(json.dumps(audit,indent=2))
 summary={k:v for k,v in report.items() if k!="rows"}
 summary["audit_file"]="xyzabc321_human_audit_v1.json"
 summary["audit_sha256"]=audit["sample_sha256"]
 print(json.dumps(summary,indent=2))
