from dataclasses import dataclass, asdict
import hashlib, json
from temperans.workstate_normalizer import WorkStateNormalizer
VALID={"attach","branch","new","uncertain"}
@dataclass
class SemanticRecoveryDecision:
    decision:str; confidence:float; candidate_id:str|None; provider:str; reasons:list
    def to_dict(self): return asdict(self)

def semantic_signature(t,c,evidence):
    raw=json.dumps({"trajectory":t.to_dict(),"conversation":c.to_dict(),"evidence":evidence or {}},sort_keys=True,separators=(",",":"),ensure_ascii=False,default=str)
    return hashlib.sha256(raw.encode()).hexdigest()

class SemanticRecoveryEngine:
    def __init__(self,judge,provider="unknown",min_confidence=.80,cache=None):
        self.judge=judge; self.provider=provider; self.min_confidence=min_confidence; self.cache=cache; self.normalizer=WorkStateNormalizer()
    def recover(self,trajectory,conversation,structural_evidence=None):
        t=self.normalizer.trajectory(trajectory); c=self.normalizer.conversation(conversation)
        sig=semantic_signature(t,c,structural_evidence)
        if self.cache:
            x=self.cache.get(sig)
            if x: return SemanticRecoveryDecision(x["decision"],float(x["confidence"]),x.get("candidate_id"),x.get("provider",self.provider),list(x.get("reasons",[])))
        result=self.judge.judge(trajectory=trajectory,conversation=conversation,structural_evidence=structural_evidence)
        provider=self.provider
        if isinstance(result,tuple) and len(result)==3:
            result,p,_=result; provider=p or provider
        if result is None:
            d=SemanticRecoveryDecision("uncertain",0.0,getattr(trajectory,"trajectory_id",None),provider,["no semantic judge result"])
        else:
            label=str(result.decision).lower().strip(); conf=float(result.confidence)
            if label not in VALID: label="uncertain"
            if label!="uncertain" and conf<self.min_confidence: label="uncertain"
            d=SemanticRecoveryDecision(label,conf,getattr(trajectory,"trajectory_id",None),provider,list(getattr(result,"reasons",[])))
        if self.cache: self.cache.put({"signature":sig,**d.to_dict()})
        return d
