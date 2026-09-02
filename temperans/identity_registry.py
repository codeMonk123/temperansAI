import json,uuid
from pathlib import Path
class IdentityRegistry:
    def __init__(self,path):
        self.path=Path(path); self.links={}; self._load()
    def _load(self):
        if not self.path.exists(): return
        for x in json.loads(self.path.read_text()).get("links",[]):
            self.links[(x["workspace_id"],x["surface"],x["external_user_id"])]=x["person_id"]
    def _save(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        rows=[{"workspace_id":w,"surface":s,"external_user_id":e,"person_id":p} for (w,s,e),p in sorted(self.links.items())]
        self.path.write_text(json.dumps({"links":rows},indent=2))
    def link(self,workspace_id,surface,external_user_id,person_id):
        k=(workspace_id,surface,external_user_id); old=self.links.get(k)
        if old and old!=person_id: raise ValueError("identity already linked to "+old)
        self.links[k]=person_id; self._save(); return {"workspace_id":workspace_id,"surface":surface,"external_user_id":external_user_id,"person_id":person_id}
    def resolve(self,workspace_id,surface,external_user_id,create=True):
        k=(workspace_id,surface,external_user_id)
        if k in self.links: return self.links[k]
        if not create: return None
        p="person_"+uuid.uuid4().hex[:16]; self.links[k]=p; self._save(); return p
