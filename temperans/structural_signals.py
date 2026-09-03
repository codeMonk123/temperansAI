"""Deterministic L1 signal emission from persisted trajectory state/delta."""
import json
from pathlib import Path
from temperans.signals import SignalObservation

class StructuralSignalEngine:
    PRODUCER_VERSION="structural-signals-v1"
    def __init__(self,taxonomy_path="signal_taxonomy_v1.json"):
        t=json.loads(Path(taxonomy_path).read_text())
        self.version=t["taxonomy_version"];self.sha=t["taxonomy_sha256"]
    def _s(self,name,value,evidence):
        return SignalObservation("temperans."+name,value,"L1",self.version,self.sha,
            self.PRODUCER_VERSION,["state_delta","trajectory_state"],evidence)
    def emit(self,state_delta,trajectory):
        d=state_delta or {}; fields=d.get("fields",{})
        out=[
          self._s("trajectory_created",bool(d.get("trajectory_created")),["state_delta"]),
          self._s("state_changed",bool(d),["state_delta"]),
          self._s("durable_goal_changed","durable_goal" in fields,["durable_goal"]),
          self._s("structurally_inert",not bool(d),["state_delta"]),
          self._s("failure_count",len(trajectory.get("failures",[])),["failures"]),
          self._s("attempt_count",len(trajectory.get("attempts",[])),["attempts"]),
          self._s("unresolved_question_count",len(trajectory.get("open_questions",[])),["open_questions"]),
          self._s("surface_count",len(set(trajectory.get("surfaces",[]))),["surfaces"]),
        ]
        before=(fields.get("surfaces") or {}).get("from") or []
        after=(fields.get("surfaces") or {}).get("to") or []
        out.append(self._s("cross_surface_continuation",
            bool(before and len(set(after))>len(set(before))),["surfaces"]))
        return out
