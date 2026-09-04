"""Conservative authority gate for anchorless semantic recovery.
A single L2 model is NEVER sufficient to authorize anchorless ATTACH.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class SemanticRecoveryDecision:
    action: str
    candidate_id: str | None
    accepted: bool
    reason: str

def decide_semantic_recovery(primary, verifier, candidate_id, min_confidence=.80):
    if primary is None:
        return SemanticRecoveryDecision("clarify",None,False,"primary_unavailable")
    if primary.action == "abstain":
        return SemanticRecoveryDecision("clarify",None,False,"primary_abstained")
    if primary.action != "attach" or primary.candidate_id != candidate_id:
        return SemanticRecoveryDecision("clarify",None,False,"primary_did_not_attach_candidate")
    if primary.confidence < min_confidence:
        return SemanticRecoveryDecision("clarify",None,False,"primary_low_confidence")
    # Anchorless attach is exactly where K3 previously false-merged. Require
    # an independent verifier rather than converting semantic similarity to authority.
    if verifier is None:
        return SemanticRecoveryDecision("clarify",None,False,"verifier_required")
    if (verifier.action != "attach" or verifier.candidate_id != candidate_id
            or verifier.confidence < min_confidence):
        return SemanticRecoveryDecision("clarify",None,False,"provider_disagreement")
    return SemanticRecoveryDecision("attach",candidate_id,True,"independent_provider_consensus")
