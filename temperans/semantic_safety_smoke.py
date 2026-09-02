from temperans.anchors import AnchorExtractor
from temperans.semantic_safety_gate import SemanticSafetyGate
from temperans.workstate import ConversationState, TrajectoryState

def make(old,new,og="",ng=""):
    x=AnchorExtractor()
    t=TrajectoryState(trajectory_id="t",workspace_id="w",person_id="u",durable_goal=og,current_state=old,anchors=x.extract(old+" "+og))
    c=ConversationState(workspace_id="w",person_id="u",conversation_id="c",surface="test",goal=ng,current_problem=new,anchors=x.extract(new+" "+ng))
    return t,c

g=SemanticSafetyGate()

t,c=make("repository service-15 fix trajectory routing","repository service-15 repair package metadata")
r=g.validate("attach",.90,t,c,.70,.20,True)
assert not r.accepted and r.decision=="uncertain", r

t,c=make("production deployment failing","service dies during startup","restore deployment","restore deployment")
r=g.validate("attach",.90,t,c,.70,.20,True)
assert r.accepted and r.decision=="attach", r

t,c=make("Investigating PROD-218","Update PROD-218 service starts")
r=g.validate("attach",.90,t,c,.30,.70,False)
assert r.accepted and r.decision=="attach", r

print("SEMANTIC SAFETY SMOKE: PASS")
