import hashlib,json
from pathlib import Path
class IdempotencyConflict(ValueError): pass
def digest(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
class IdempotencyStore:
    def __init__(self,path):
        self.path=Path(path); self.items=json.loads(self.path.read_text()) if self.path.exists() else {}
    def _save(self):
        self.path.parent.mkdir(parents=True,exist_ok=True); t=self.path.with_suffix(".tmp"); t.write_text(json.dumps(self.items,indent=2,default=str)); t.replace(self.path)
    def lookup(self,event_id,payload):
        x=self.items.get(event_id)
        if x is None:return None
        if x["hash"]!=digest(payload):raise IdempotencyConflict("event_id payload conflict")
        return x["result"]
    def commit(self,event_id,payload,result):
        old=self.lookup(event_id,payload)
        if old is not None:return old
        self.items[event_id]={"hash":digest(payload),"result":result}; self._save(); return result
