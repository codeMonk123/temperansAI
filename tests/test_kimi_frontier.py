import pytest
from temperans.candidate_assessment import CandidateAssessment
from temperans.frontier_scoring import choose
def test_candidate_assessment_is_l2():
 x=CandidateAssessment("t",.8,.1,.1,.9,["ticket"])
 assert x.maturity=="L2" and choose([x])=="t"
def test_candidate_assessment_rejects_authority():
 with pytest.raises(ValueError):CandidateAssessment("t",.8,.1,.1,.9,[],maturity="L1")
def test_choose_can_abstain():
 assert choose([CandidateAssessment("t",.2,.1,.7,.8,[])]) is None
