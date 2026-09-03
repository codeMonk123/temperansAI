from temperans.frontier_assessment import FrontierAssessment
from temperans.hybrid_gate_v1 import hybrid_gate
def c():
 return [{"trajectory_id":"t","anchors":[{"type":"ticket","value":"PROD-218","strength":"strong"}]}]
def e(text):return {"content":{"text":text}}
def test_attach_requires_structural_support():
 a=FrontierAssessment("attach","t",.95)
 assert hybrid_gate(e("PROD-218 still broken"),c(),a).action=="attach"
 assert hybrid_gate(e("warehouse rows still low"),c(),a).action=="clarify"
def test_new_high_confidence_can_be_accepted():
 assert hybrid_gate(e("new issue"),c(),FrontierAssessment("new",None,.9)).action=="new"
def test_abstain_stays_clarify():
 assert hybrid_gate(e("same thing"),c(),FrontierAssessment("abstain",None,.9)).action=="clarify"
def test_branch_requires_anchor():
 a=FrontierAssessment("branch","t",.9)
 assert hybrid_gate(e("PROD-218 related follow-up"),c(),a).action=="branch"
 assert hybrid_gate(e("related follow-up"),c(),a).action=="clarify"
