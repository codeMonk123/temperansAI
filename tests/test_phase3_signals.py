import json
from temperans.structural_signals import StructuralSignalEngine
from temperans.signal_store import SQLiteSignalStore
from temperans.platform import TemperansPlatform
from temperans.perception_provider import PerceptionRequest,PerceptionResult
from temperans.signals import SignalObservation
from temperans.model_evaluation import evaluate_provider

def test_structural_signals_are_l1_and_deterministic():
 e=StructuralSignalEngine()
 t={"failures":["f"],"attempts":["a","b"],"open_questions":[],"surfaces":["slack","chat"]}
 d={"fields":{"current_state":{"from":"x","to":"y"},"surfaces":{"from":["slack"],"to":["slack","chat"]}}}
 a=e.emit(d,t);b=e.emit(d,t)
 assert [x.to_dict() for x in a]==[x.to_dict() for x in b]
 assert all(x.maturity=="L1" and x.policy_eligible for x in a)
 vals={x.signal:x.value for x in a}
 assert vals["temperans.failure_count"]==1
 assert vals["temperans.cross_surface_continuation"] is True

def test_signal_persistence_is_tenant_scoped(tmp_path):
 p=TemperansPlatform(tmp_path/"p");p.create_organization(organization_id="a",name="a");p.create_organization(organization_id="b",name="b")
 sa=SQLiteSignalStore(p.runtime("a").sqlite,"a");sb=SQLiteSignalStore(p.runtime("b").sqlite,"b")
 sig=StructuralSignalEngine().emit({},{"failures":[],"attempts":[],"open_questions":[],"surfaces":[]})
 sa.persist("e","t",sig)
 assert len(sa.list())==len(sig) and sb.list()==[]

def test_model_evaluation_rejects_authoritative_model_signal():
 class Bad:
  def perceive(self,r):
   return PerceptionResult("x","x","x",[SignalObservation("temperans.state_changed",True,"L1","1","h","x")])
 try:evaluate_provider(Bad(),PerceptionRequest(event={},candidate_views=[]));assert False
 except RuntimeError:pass
