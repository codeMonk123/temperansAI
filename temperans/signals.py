from dataclasses import dataclass,field,asdict
from typing import Any
@dataclass(frozen=True)
class SignalObservation:
    signal:str; value:Any; maturity:str; taxonomy_version:str; taxonomy_sha256:str; producer_version:str
    provenance:list[str]=field(default_factory=list); evidence:list=field(default_factory=list); confidence:float|None=None
    def to_dict(self):return asdict(self)
    @property
    def policy_eligible(self):return self.maturity in {"L0","L1","L3"}
def weakest_maturity(*xs):
    if not xs:raise ValueError("maturity required")
    if "L2" in xs:return "L2"
    if "L1" in xs:return "L1"
    if "L0" in xs:return "L0"
    if all(x=="L3" for x in xs):return "L3"
    raise ValueError("unknown maturity")
def require_policy_eligible(s):
    if not s.policy_eligible:raise PermissionError("L2 signal is not policy eligible")
    return s
