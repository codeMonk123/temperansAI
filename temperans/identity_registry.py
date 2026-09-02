import json
import uuid
from pathlib import Path

class IdentityRegistry:
    def __init__(self,path,organization_id="default"):
        self.path=Path(path); self.organization_id=organization_id; self.links={}; self._load()
    def _key(self,w,s,e): return (self.organization_id,str(w),str(s),str(e))
    def _load(self):
        if not self.path.exists(): return
        for x in json.loads(self.path.read_text()).get("links",[]):
            self.links[(x.get("organization_id",self.organization_id),x["workspace_id"],x["surface"],x["external_user_id"])]=x["person_id"]
    def _save(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        rows=[{"organization_id":o,"workspace_id":w,"surface":s,"external_user_id":e,"person_id":person} for (o,w,s,e),person in sorted(self.links.items())]
        tmp=self.path.with_suffix(".tmp"); tmp.write_text(json.dumps({"links":rows},indent=2)); tmp.replace(self.path)
    def link(self,workspace_id,surface,external_user_id,person_id):
        k=self._key(workspace_id,surface,external_user_id); old=self.links.get(k)
        if old and old!=person_id: raise ValueError("identity already linked")
        self.links[k]=person_id; self._save(); return {"organization_id":self.organization_id,"workspace_id":workspace_id,"surface":surface,"external_user_id":external_user_id,"person_id":person_id}
    def resolve(self,workspace_id,surface,external_user_id,create=True):
        k=self._key(workspace_id,surface,external_user_id)
        if k in self.links:return self.links[k]
        if not create:return None
        person="person_"+uuid.uuid4().hex[:16]; self.links[k]=person; self._save(); return person
