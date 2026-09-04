"""Semantic Recovery V1 eligibility.
This module does not mutate trajectories and does not change deterministic thresholds.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class RecoveryEligibility:
    eligible: bool
    reason: str

def semantic_recovery_eligibility(*, deterministic_result, candidate_count,
                                  top_anchor_relevant, linker_decision):
    if deterministic_result.get("decision") != "clarify":
        return RecoveryEligibility(False, "deterministic_not_clarify")
    if candidate_count != 1:
        return RecoveryEligibility(False, "requires_exactly_one_candidate")
    if top_anchor_relevant:
        return RecoveryEligibility(False, "structural_path_should_handle_anchor")
    if linker_decision != "uncertain":
        return RecoveryEligibility(False, "linker_not_uncertain")
    return RecoveryEligibility(True, "single_candidate_anchorless_uncertain")
