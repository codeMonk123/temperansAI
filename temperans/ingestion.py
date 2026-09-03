"""Historical import and replay adapters. Both call the same runtime.observe()."""
from dataclasses import dataclass
from datetime import datetime

def _key(e):
    occurred=e.get("occurred_at") or ""
    seq=e.get("source_sequence")
    try: seq_key=(0,int(seq))
    except (TypeError,ValueError): seq_key=(1,str(seq or ""))
    return (occurred,seq_key,str(e.get("event_id","")))

@dataclass
class IngestionRun:
    path:str
    results:list
    event_count:int

def import_events(runtime,events):
    rows=sorted([dict(x) for x in events],key=_key)
    return IngestionRun("import",[runtime.observe(x) for x in rows],len(rows))

def replay_events(runtime,events):
    rows=sorted([dict(x) for x in events],key=_key)
    return IngestionRun("replay",[runtime.observe(x) for x in rows],len(rows))
