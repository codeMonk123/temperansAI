import json,tempfile
from temperans.platform import TemperansPlatform
from temperans.xyzabc321_dataset import build_xyzabc321
from temperans.xyzabc321_evaluator import evaluate
with tempfile.TemporaryDirectory() as d:
 p=TemperansPlatform(d); p.create_organization(organization_id="XYZABC321",name="XYZABC321 Inc.")
 events,_=build_xyzabc321()
 print(json.dumps(evaluate(p.runtime("XYZABC321"),events),indent=2,sort_keys=True))
