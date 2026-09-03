import json
from pathlib import Path
import pytest
from temperans.state_normalization import normalized_trajectory_state,compare_normalized
from temperans.signals import SignalObservation,require_policy_eligible,weakest_maturity
def test_normalization():
 a={"trajectory_id":"x","durable_goal":"g","current_state":"a","lifecycle":"active","trajectory_version":9}
 b={**a,"trajectory_id":"y","trajectory_version":1}
 assert "trajectory_id" not in normalized_trajectory_state(a)
 assert compare_normalized([a],[b])["equivalent"]
 b["current_state"]="b";assert not compare_normalized([a],[b])["equivalent"]
def test_taxonomy_and_policy():
 t=json.loads(Path("signal_taxonomy_v1.json").read_text());assert len(t["taxonomy_sha256"])==64
 names=[x["name"] for x in t["signals"]];assert len(names)==len(set(names))
 l2=SignalObservation("temperans.frustration",.8,"L2",t["taxonomy_version"],t["taxonomy_sha256"],"test",["model"])
 with pytest.raises(PermissionError):require_policy_eligible(l2)
 assert weakest_maturity("L1","L2")=="L2"
