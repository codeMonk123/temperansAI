from temperans.xyzabc321_dataset import build_xyzabc321
from temperans.xyzabc321_evaluator import evaluate
from temperans.platform import TemperansPlatform
def test_xyzabc321_shape():
 events,gold=build_xyzabc321()
 assert len(events)==120 and len(gold)==60
 assert len({e["external_user_id"] for e in events})==20
 assert len({e["surface"] for e in events})>=3
def test_xyzabc321_runs_end_to_end(tmp_path):
 p=TemperansPlatform(tmp_path/"p"); p.create_organization(organization_id="XYZABC321",name="XYZABC321")
 events,_=build_xyzabc321(); r=evaluate(p.runtime("XYZABC321"),events)
 assert r["events"]==120 and r["gold_trajectories"]==60
 assert 0<=r["trajectory_pair_recall"]<=1
