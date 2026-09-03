import pytest
from temperans.frontier_assessment import FrontierAssessment
def test_frontier_actions():
 assert FrontierAssessment("new",None,.9).maturity=="L2"
 assert FrontierAssessment("attach","t",.9).candidate_id=="t"
def test_invalid_candidate_contract():
 with pytest.raises(ValueError):FrontierAssessment("attach",None,.9)
 with pytest.raises(ValueError):FrontierAssessment("new","t",.9)
