import json,uuid
from pathlib import Path
from datetime import datetime,timezone
def now(): return datetime.now(timezone.utc).isoformat()
class PilotStore:
    def __init__(self,root):
        self.root=Path(root); self.root.mkdir(parents=True,exist_ok=True)
    def _append(self,name,row):
        with (self.root/name).open("a",encoding="utf-8") as f:
            f.write(json.dumps(row,ensure_ascii=False,default=str)+"\n")
    def event(self,row):
        x={"record_id":"evt_"+uuid.uuid4().hex[:16],"recorded_at":now(),**row}; self._append("events.jsonl",x); return x
    def decision(self,row):
        x={"record_id":"dec_"+uuid.uuid4().hex[:16],"recorded_at":now(),**row}; self._append("decisions.jsonl",x); return x
    def correction(self,row):
        x={"correction_id":"cor_"+uuid.uuid4().hex[:16],"recorded_at":now(),**row}; self._append("corrections.jsonl",x); return x
    def read(self,name):
        p=self.root/name
        if not p.exists(): return []
        return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
