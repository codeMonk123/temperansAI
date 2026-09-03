from datetime import datetime
def _parse(x):
 if not x:return None
 return datetime.fromisoformat(str(x).replace("Z","+00:00"))
def classify_late_event(sqlite,organization_id,event):
 occurred=_parse(event.occurred_at)
 if occurred is None:return {"late_event":False,"history_disordered":False,"recompute_recommended":False}
 row=sqlite.conn.execute("SELECT occurred_at FROM events WHERE organization_id=? AND occurred_at IS NOT NULL ORDER BY occurred_at DESC LIMIT 1",(organization_id,)).fetchone()
 latest=_parse(row["occurred_at"]) if row else None
 late=bool(latest and occurred<latest)
 return {"late_event":late,"history_disordered":late,"recompute_recommended":late}
