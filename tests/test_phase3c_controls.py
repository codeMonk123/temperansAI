from temperans.routing_control import apply_routing_mode
from temperans.concurrency_recovery import observe_with_concurrency_recovery
from temperans.sqlite_store import ConcurrentTrajectoryUpdate

def test_clarify_only_contains_mutating_proposal():
 r=apply_routing_mode("clarify_only",{"decision":"attach","trajectory_id":"t"})
 assert r["decision"]=="clarify" and r["proposed_decision"]=="attach"
 assert r["requires_confirmation"] is True

def test_automatic_preserves_decision():
 r=apply_routing_mode("automatic",{"decision":"attach"})
 assert r["decision"]=="attach" and r["requires_confirmation"] is False

def test_concurrency_recovery_retries_once():
 class S:
  audit_store=None
  def __init__(self):self.n=0
  def observe(self,data,event_id=None):
   self.n+=1
   if self.n==1:raise ConcurrentTrajectoryUpdate("stale")
   return {"decision":"attach"}
 s=S()
 assert observe_with_concurrency_recovery(s,{}, "e")["decision"]=="attach"
 assert s.n==2
