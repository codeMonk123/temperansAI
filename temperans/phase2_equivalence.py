from temperans.ingestion import import_events,replay_events
from temperans.ingestion_equivalence import IngestionState,assert_ingestion_equivalent
def states(r):
 return [x["state"] for x in r.sqlite.list_trajectories(organization_id=r.config.organization_id)]
def run_live(r,events):
 [r.observe(dict(e)) for e in events];return IngestionState("live",states(r),{"event_count":len(events)})
def run_import(r,events):
 x=import_events(r,events);return IngestionState("import",states(r),{"event_count":x.event_count})
def run_replay(r,events):
 x=replay_events(r,events);return IngestionState("replay",states(r),{"event_count":x.event_count})
def assert_three_path_equivalence(live,imported,replayed,events):
 return assert_ingestion_equivalent(live=run_live(live,events),imported=run_import(imported,events),replayed=run_replay(replayed,events))
