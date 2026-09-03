"""Provider-neutral consensus rule. Model agreement is evidence, never authority."""
from dataclasses import dataclass
@dataclass(frozen=True)
class ConsensusResult:
 action:str
 candidate_id:str|None
 agreement:bool
 reason:str
def consensus(a,b,min_confidence=.80):
 if a.maturity!="L2" or b.maturity!="L2":raise ValueError("consensus inputs must be L2")
 same=(a.action,a.candidate_id)==(b.action,b.candidate_id)
 if not same:return ConsensusResult("clarify",None,False,"provider_disagreement")
 if a.action=="abstain":return ConsensusResult("clarify",None,True,"providers_abstain")
 if min(a.confidence,b.confidence)<min_confidence:return ConsensusResult("clarify",None,True,"agreement_low_confidence")
 return ConsensusResult(a.action,a.candidate_id,True,"high_confidence_provider_agreement")
