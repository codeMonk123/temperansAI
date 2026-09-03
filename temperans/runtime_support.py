from temperans.signal_store import SQLiteSignalStore
from temperans.structural_signals import StructuralSignalEngine
from temperans.sqlite_store import ConcurrentTrajectoryUpdate
INSTRUMENTATION_VERSION="runtime-instrumentation-v1"
class RuntimeSignalSupport:
 def __init__(self,sqlite,organization_id):
  self.engine=StructuralSignalEngine();self.store=SQLiteSignalStore(sqlite,organization_id)
 def record(self,event_id,trajectory_id,state_delta,trajectory):
  signals=self.engine.emit(state_delta,trajectory or {})
  ids=self.store.persist(event_id,trajectory_id,signals)
  return [s.to_dict() for s in signals],ids
def instrumentation(result,trajectory_version=None):
 trace=result.get("trace") or {}
 return {"instrumentation_version":INSTRUMENTATION_VERSION,"trajectory_version":trajectory_version,
 "decision":result.get("decision"),"source":result.get("source"),"confidence":result.get("confidence"),
 "candidate_score":trace.get("candidate_score"),"second_score":trace.get("second_score"),
 "margin":trace.get("margin"),"rules":trace.get("rules",[]),"input_signature":trace.get("input_signature")}
def with_concurrency_retry(fn,reload_fn,max_retries=1):
 for attempt in range(max_retries+1):
  try:return fn()
  except ConcurrentTrajectoryUpdate:
   if attempt>=max_retries:raise
   reload_fn()
