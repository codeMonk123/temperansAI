"""Development/validation recovery engine. Does not alter deterministic thresholds."""
from temperans.semantic_new_recovery import decide_new

class ConsensusNewRecovery:
    def __init__(self,primary,verifier):
        self.primary=primary;self.verifier=verifier

    def assess(self,event,candidates):
        try:p,_=self.primary.assess(event,candidates)
        except Exception:return {"accepted":False,"action":"clarify","reason":"primary_unavailable"}
        if p.action!="new" or p.confidence<.80:
            return {"accepted":False,"action":"clarify","reason":"primary_not_confident_new"}
        try:v,_=self.verifier.assess(event,candidates)
        except Exception:return {"accepted":False,"action":"clarify","reason":"verifier_unavailable"}
        d=decide_new(p,v)
        return {"accepted":d.accepted,"action":d.action,"reason":d.reason,
                "primary":p.to_dict(),"verifier":v.to_dict()}
