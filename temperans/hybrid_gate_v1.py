"""Hybrid Frontier Gate V1.
K3 remains L2. Structural evidence controls authority.
"""
from dataclasses import dataclass,asdict

@dataclass(frozen=True)
class HybridGateResult:
 action:str
 candidate_id:str|None
 source:str
 reason:str
 accepted_model:bool
 def to_dict(self):return asdict(self)

def _anchors(candidate):
 return {(str(a.get("type","")).lower(),str(a.get("value","")).lower())
         for a in candidate.get("anchors",[]) if isinstance(a,dict)}

def _event_anchor_values(event):
 text=str((event.get("content") or {}).get("text","")).lower()
 vals=set()
 for token in text.replace(","," ").replace("."," ").split():
  if "-" in token and any(ch.isdigit() for ch in token):
   vals.add(token.strip("()[]{}:;!?"))
 return vals

def structural_support(event,candidate):
 event_vals=_event_anchor_values(event)
 cand_vals={v for _,v in _anchors(candidate)}
 exact=bool(event_vals & cand_vals)
 return {"exact_anchor":exact,"event_anchor_values":sorted(event_vals),
         "candidate_anchor_values":sorted(cand_vals)}

def hybrid_gate(event,candidates,assessment):
 if assessment.maturity!="L2":
  raise ValueError("model assessment must remain L2")
 if assessment.action=="abstain":
  return HybridGateResult("clarify",None,"hybrid_gate","model_abstained",False)
 if assessment.action=="new":
  # NEW cannot merge unrelated histories; accept only when model itself is confident.
  if assessment.confidence>=0.80:
   return HybridGateResult("new",None,"hybrid_gate","high_confidence_new",True)
  return HybridGateResult("clarify",None,"hybrid_gate","low_confidence_new",False)
 candidate=next((c for c in candidates if c.get("trajectory_id")==assessment.candidate_id),None)
 if candidate is None:
  return HybridGateResult("clarify",None,"hybrid_gate","candidate_missing",False)
 support=structural_support(event,candidate)
 if assessment.action=="attach":
  if support["exact_anchor"] and assessment.confidence>=0.75:
   return HybridGateResult("attach",assessment.candidate_id,"hybrid_gate","exact_anchor_support",True)
  return HybridGateResult("clarify",None,"hybrid_gate","attach_lacks_structural_support",False)
 if assessment.action=="branch":
  # Branch is structurally riskier than NEW and requires explicit relation evidence.
  if support["exact_anchor"] and assessment.confidence>=0.80:
   return HybridGateResult("branch",assessment.candidate_id,"hybrid_gate","branch_anchor_support",True)
  return HybridGateResult("clarify",None,"hybrid_gate","branch_lacks_structural_support",False)
 return HybridGateResult("clarify",None,"hybrid_gate","unsupported_action",False)
