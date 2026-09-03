"""Controlled XYZABC321 same-surface probe. Does not modify the frozen corpus."""
import json,tempfile
from temperans.platform import TemperansPlatform
from temperans.xyzabc321_dataset import build_xyzabc321
from temperans.xyzabc321_evaluator import evaluate

events,_=build_xyzabc321()
probe=[]
for e in events:
    x=dict(e)
    x["surface"]="generic_chatbot"
    probe.append(x)

with tempfile.TemporaryDirectory() as d:
    p=TemperansPlatform(d)
    p.create_organization(organization_id="XYZABC321_PROBE",name="XYZABC321 Same Surface Probe")
    report=evaluate(p.runtime("XYZABC321_PROBE"),probe)
    report["probe"]="same_surface_identity_control"
    print(json.dumps(report,indent=2,sort_keys=True))
