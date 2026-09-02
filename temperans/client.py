import json
from urllib.request import Request,urlopen
from urllib.parse import urlencode

class TemperansClient:
    def __init__(self,base_url="http://127.0.0.1:8765",api_key=None,timeout=10):
        self.base_url=base_url.rstrip("/"); self.api_key=api_key; self.timeout=timeout
    def _call(self,method,path,payload=None):
        headers={"Content-Type":"application/json"}
        if self.api_key: headers["Authorization"]="Bearer "+self.api_key
        req=Request(self.base_url+path,data=json.dumps(payload).encode() if payload is not None else None,method=method,headers=headers)
        with urlopen(req,timeout=self.timeout) as r: return json.loads(r.read().decode())
    def observe(self,workspace_id,person_id,conversation_id,surface,message,goal="",**extra):
        return self._call("POST","/api/observe",{"workspace_id":workspace_id,"person_id":person_id,
            "conversation_id":conversation_id,"surface":surface,"current_problem":message,"goal":goal,**extra})
    def correct(self,**payload): return self._call("POST","/api/correct",payload)
    def trajectories(self,workspace_id,person_id):
        return self._call("GET","/api/trajectories?"+urlencode({"workspace_id":workspace_id,"person_id":person_id}))
