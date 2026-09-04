import json,tempfile
from collections import Counter
from temperans.platform import TemperansPlatform
from temperans.xyzabc321_dataset import build_xyzabc321
from temperans.xyzabc321_identity import link_xyzabc321_identities
def clean(e):x=dict(e);x.pop("_gold_trajectory",None);return x
with tempfile.TemporaryDirectory() as d:
 p=TemperansPlatform(d);p.create_organization(organization_id="XYZABC321",name="XYZABC321");rt=p.runtime("XYZABC321");link_xyzabc321_identities(rt);events,_=build_xyzabc321();rows=[]
 for e in events:
  r=rt.observe(clean(e))
  if r["decision"]=="clarify":
   t=r.get("trace") or {};rows.append({"event_id":e["event_id"],"gold":e["_gold_trajectory"],"top":t.get("top_score"),"second":t.get("second_score"),"margin":t.get("margin"),"rules":t.get("rules",[])})
 def band(x):
  if x is None:return "missing"
  if x<.12:return "<.12"
  if x<.30:return ".12-.30"
  if x<.50:return ".30-.50"
  if x<.70:return ".50-.70"
  return ">=.70"
 report={"clarifications":len(rows),"top_score_bands":dict(Counter(band(r["top"]) for r in rows)),"margin_bands":dict(Counter(band(r["margin"]) for r in rows)),"rows":rows}
 open("xyzabc321_deep_diagnostic.json","w").write(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!="rows"},indent=2))
