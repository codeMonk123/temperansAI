from dataclasses import dataclass,field,asdict
@dataclass(frozen=True)
class FrontierAssessment:
 action:str
 candidate_id:str|None
 confidence:float
 evidence:list=field(default_factory=list)
 maturity:str="L2"
 def __post_init__(self):
  if self.action not in {"new","attach","branch","abstain"}:raise ValueError("invalid frontier action")
  if self.action in {"attach","branch"} and not self.candidate_id:raise ValueError("candidate required")
  if self.action in {"new","abstain"} and self.candidate_id is not None:raise ValueError("candidate must be null")
  if self.maturity!="L2":raise ValueError("frontier assessment must remain L2")
  if not 0<=float(self.confidence)<=1:raise ValueError("confidence must be 0..1")
 def to_dict(self):return asdict(self)
