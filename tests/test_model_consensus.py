from temperans.frontier_assessment import FrontierAssessment
from temperans.model_consensus import consensus
def test_disagreement_clarifies():
 a=FrontierAssessment("new",None,.9);b=FrontierAssessment("attach","t",.9)
 assert consensus(a,b).action=="clarify"
def test_high_confidence_agreement_proposes():
 a=FrontierAssessment("attach","t",.9);b=FrontierAssessment("attach","t",.95)
 r=consensus(a,b);assert r.action=="attach" and r.agreement
def test_agreed_abstain_clarifies():
 a=FrontierAssessment("abstain",None,.9);b=FrontierAssessment("abstain",None,.9)
 assert consensus(a,b).action=="clarify"
