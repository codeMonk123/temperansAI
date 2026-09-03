from dataclasses import dataclass
VALID_MODES={"clarify_only","assisted","automatic"}
@dataclass(frozen=True)
class RoutingModeDecision:
 mode:str
 requires_confirmation:bool
 proposed_decision:str|None
def apply_routing_mode(mode,result):
 if mode not in VALID_MODES:raise ValueError("invalid routing mode")
 decision=result.get("decision")
 # Safe V1: clarify_only converts mutating routing proposals to clarification.
 if mode=="clarify_only" and decision in {"new","attach","branch"}:
  x=dict(result)
  x["proposed_decision"]=decision
  x["decision"]="clarify"
  x["requires_confirmation"]=True
  x["routing_mode"]=mode
  return x
 x=dict(result);x["requires_confirmation"]=False;x["routing_mode"]=mode
 return x
