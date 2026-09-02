from temperans.client import TemperansClient

class TemperansChatbot:
    def __init__(self,workspace_id,surface,base_url="http://127.0.0.1:8765",api_key=None):
        self.workspace_id=workspace_id; self.surface=surface
        self.client=TemperansClient(base_url,api_key)
    def before_reply(self,person_id,conversation_id,message,goal="",**extra):
        return self.client.observe(self.workspace_id,person_id,conversation_id,self.surface,message,goal,**extra)
    @staticmethod
    def context_text(result):
        p=result.get("context_pack") or {}
        lines=["TEMPERANS WORK CONTEXT","Goal: "+str(p.get("goal","")),
               "Current state: "+str(p.get("current_state","")),
               "Lifecycle: "+str(p.get("lifecycle",""))]
        if p.get("artifacts"): lines+=["Relevant artifacts:"]+["- "+str(x) for x in p["artifacts"]]
        if p.get("decisions"): lines+=["Prior decisions:"]+["- "+str(x) for x in p["decisions"]]
        if p.get("recent_context"): lines+=["Recent evolution:"]+["- "+str(x) for x in p["recent_context"]]
        return "\n".join(lines)
    def correct(self,result,person_id,conversation_id,action,target_trajectory_id=None,note=""):
        return self.client.correct(decision_record_id=result.get("decision_record_id"),
            workspace_id=self.workspace_id,person_id=person_id,conversation_id=conversation_id,
            original_trajectory_id=result.get("trajectory_id"),action=action,
            target_trajectory_id=target_trajectory_id,note=note)
