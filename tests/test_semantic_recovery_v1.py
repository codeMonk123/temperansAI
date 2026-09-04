from temperans.frontier_assessment import FrontierAssessment
from temperans.semantic_recovery_v1 import semantic_recovery_eligibility
from temperans.semantic_recovery_gate import decide_semantic_recovery

def A(action,cid=None,confidence=.9):
    return FrontierAssessment(action,cid,confidence)

def test_only_diagnosed_shape_is_eligible():
    r={"decision":"clarify"}
    assert semantic_recovery_eligibility(deterministic_result=r,candidate_count=1,
        top_anchor_relevant=False,linker_decision="uncertain").eligible
    assert not semantic_recovery_eligibility(deterministic_result=r,candidate_count=2,
        top_anchor_relevant=False,linker_decision="uncertain").eligible
    assert not semantic_recovery_eligibility(deterministic_result=r,candidate_count=1,
        top_anchor_relevant=True,linker_decision="uncertain").eligible

def test_single_model_can_never_authorize_anchorless_attach():
    d=decide_semantic_recovery(A("attach","t"),None,"t")
    assert d.action=="clarify" and not d.accepted

def test_independent_agreement_can_authorize():
    d=decide_semantic_recovery(A("attach","t"),A("attach","t",.95),"t")
    assert d.action=="attach" and d.accepted

def test_disagreement_stays_clarify():
    d=decide_semantic_recovery(A("attach","t"),A("new",None),"t")
    assert d.action=="clarify" and not d.accepted

def test_wrong_candidate_stays_clarify():
    d=decide_semantic_recovery(A("attach","other"),A("attach","other"),"t")
    assert d.action=="clarify"
