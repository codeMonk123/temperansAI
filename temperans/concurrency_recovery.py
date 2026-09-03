from temperans.sqlite_store import ConcurrentTrajectoryUpdate
def reload_runtime_trajectories(service):
 from temperans.trajectory_persistence import deserialize_trajectory
 if service.audit_store is None:return
 rows=service.audit_store.sqlite.list_trajectories(
  organization_id=service.audit_store.organization_id)
 service.runtime.trajectories={
  row["trajectory_id"]:deserialize_trajectory(row["state"]) for row in rows}
def observe_with_concurrency_recovery(service,data,event_id,max_retries=1):
 for attempt in range(max_retries+1):
  try:return service.observe(data,event_id=event_id)
  except ConcurrentTrajectoryUpdate:
   if attempt>=max_retries:raise
   reload_runtime_trajectories(service)
