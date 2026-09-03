import json,tempfile
from temperans.platform import TemperansPlatform
from temperans.xyzabc321_dataset import build_xyzabc321
from temperans.xyzabc321_evaluator_v2 import evaluate_v2
from temperans.xyzabc321_identity import link_xyzabc321_identities
with tempfile.TemporaryDirectory() as d:
 p=TemperansPlatform(d);p.create_organization(organization_id="XYZABC321",name="XYZABC321 Inc.")
 rt=p.runtime("XYZABC321");link_xyzabc321_identities(rt)
 events,_=build_xyzabc321()
 print(json.dumps(evaluate_v2(rt,events),indent=2,sort_keys=True))
