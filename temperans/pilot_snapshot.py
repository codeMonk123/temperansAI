import json
from pathlib import Path
from temperans.anchors import Anchor,AnchorStrength
from temperans.workstate import TrajectoryState

class TrajectorySnapshotStore:
    def __init__(self,path): self.path=Path(path)
    def save(self,trajectories):
        rows=[]
        for t in trajectories.values():
            x=t.to_dict(); x["anchors"]=[a.to_dict() for a in t.anchors]; rows.append(x)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        tmp=self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"trajectories":rows},indent=2,default=str),encoding="utf-8")
        tmp.replace(self.path)
    def load(self):
        if not self.path.exists(): return {}
        data=json.loads(self.path.read_text(encoding="utf-8")); out={}
        for x in data.get("trajectories",[]):
            anchors=[Anchor(type=a["type"],value=a["value"],strength=AnchorStrength(a["strength"])) for a in x.get("anchors",[])]
            t=TrajectoryState(
                trajectory_id=x["trajectory_id"],workspace_id=x["workspace_id"],person_id=x["person_id"],
                durable_goal=x.get("durable_goal",""),current_state=x.get("current_state",""),
                lifecycle=x.get("lifecycle","active"),entities=x.get("entities",[]),artifacts=x.get("artifacts",[]),
                anchors=anchors,open_questions=x.get("open_questions",[]),resolved_questions=x.get("resolved_questions",[]),
                decisions=x.get("decisions",[]),attempts=x.get("attempts",[]),failures=x.get("failures",[]),
                outcomes=x.get("outcomes",[]),surfaces=x.get("surfaces",[]),conversation_ids=x.get("conversation_ids",[]),
                recent_context=x.get("recent_context",[]))
            out[t.trajectory_id]=t
        return out
