"""Provider-neutral semantic recovery service."""
from temperans.semantic_recovery_v1 import semantic_recovery_eligibility
from temperans.semantic_recovery_gate import decide_semantic_recovery

class SemanticRecoveryService:
    def __init__(self, primary, verifier):
        self.primary=primary
        self.verifier=verifier

    def assess(self, *, event, candidate_views, deterministic_result,
               top_anchor_relevant, linker_decision):
        elig=semantic_recovery_eligibility(
            deterministic_result=deterministic_result,
            candidate_count=len(candidate_views),
            top_anchor_relevant=top_anchor_relevant,
            linker_decision=linker_decision)
        if not elig.eligible:
            return {"eligible":False,"decision":"clarify","reason":elig.reason}
        candidate_id=candidate_views[0]["trajectory_id"]
        p,_=self.primary.assess(event,candidate_views) if self.primary else (None,{})
        # Do not spend verifier call unless primary proposes the exact ATTACH.
        if p is None or p.action!="attach" or p.candidate_id!=candidate_id:
            d=decide_semantic_recovery(p,None,candidate_id)
            return {"eligible":True,"decision":d.action,"candidate_id":d.candidate_id,
                    "accepted":d.accepted,"reason":d.reason}
        v,_=self.verifier.assess(event,candidate_views) if self.verifier else (None,{})
        d=decide_semantic_recovery(p,v,candidate_id)
        return {"eligible":True,"decision":d.action,"candidate_id":d.candidate_id,
                "accepted":d.accepted,"reason":d.reason,
                "primary":p.to_dict(),"verifier":v.to_dict() if v else None}
