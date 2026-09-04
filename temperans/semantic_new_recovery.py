"""Consensus NEW recovery for deterministic single-candidate abstentions."""
from dataclasses import dataclass

@dataclass(frozen=True)
class NewRecovery:
    accepted: bool
    action: str
    reason: str

def decide_new(primary, verifier, min_confidence=.80):
    if primary is None: return NewRecovery(False,"clarify","primary_unavailable")
    if primary.action!="new" or primary.confidence<min_confidence:
        return NewRecovery(False,"clarify","primary_not_confident_new")
    if verifier is None: return NewRecovery(False,"clarify","verifier_required")
    if verifier.action!="new" or verifier.confidence<min_confidence:
        return NewRecovery(False,"clarify","provider_disagreement")
    return NewRecovery(True,"new","independent_provider_consensus")
