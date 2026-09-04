from temperans.semantic_new_recovery import decide_new
from temperans.frontier_assessment import FrontierAssessment
from temperans.milestone_a import score

def A(action, confidence=.9, candidate_id=None):
    if action in {"attach","branch"} and candidate_id is None:
        candidate_id="candidate_t"
    return FrontierAssessment(action,candidate_id,confidence)

def test_consensus_new():
    assert decide_new(A("new"),A("new")).accepted

def test_one_model_not_authority():
    assert not decide_new(A("new"),None).accepted

def test_disagreement_clarifies():
    assert not decide_new(A("new"),A("attach")).accepted

def test_machine_gate():
    assert score(
        trajectory_reconstruction_rate=.7,
        false_merges=0,
        human_correct_rate=.7,
        human_false_merges=0,
    )["milestone_a_pass"]

def test_false_merge_blocks():
    assert not score(
        trajectory_reconstruction_rate=1,
        false_merges=1,
        human_correct_rate=1,
        human_false_merges=0,
    )["milestone_a_pass"]
