from temperans.client import TemperansClient
class SurfaceClient:
    def __init__(self,workspace_id,surface,base_url="http://127.0.0.1:8765"):
        self.workspace_id=workspace_id; self.surface=surface; self.client=TemperansClient(base_url)
    def observe(self,external_user_id,conversation_id,message,goal="",**extra):
        return self.client._call("POST","/api/observe",{"workspace_id":self.workspace_id,"surface":self.surface,
            "external_user_id":external_user_id,"conversation_id":conversation_id,"current_problem":message,"goal":goal,**extra})
