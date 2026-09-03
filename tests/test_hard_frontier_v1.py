from collections import Counter
from temperans.hard_frontier_v1 import build_hard_frontier

def test_hard_frontier_shape_and_balance():
    c=build_hard_frontier()
    assert len(c)==40
    actions=Counter(x["gold_action"] for x in c)
    assert actions=={"new":10,"attach":15,"branch":5,"abstain":10}
    assert len({x["case_id"] for x in c})==40

def test_candidate_contract_matches_gold():
    for c in build_hard_frontier():
        ids={x["trajectory_id"] for x in c["candidate_views"]}
        if c["gold_action"] in {"attach","branch"}:
            assert c["gold_candidate_id"] in ids
        else:
            assert c["gold_candidate_id"] is None

def test_hard_frontier_has_eight_categories():
    assert len({x["category"] for x in build_hard_frontier()})==8
