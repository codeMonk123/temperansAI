from dataclasses import dataclass,field,asdict
@dataclass(frozen=True)
class CandidateAssessment:
 candidate_id:str
 same_work:float
 branch:float
 unrelated:float
 confidence:float
 evidence:list=field(default_factory=list)
 maturity:str="L2"
 def __post_init__(self):
  if self.maturity!="L2":raise ValueError("CandidateAssessment must remain L2")
  for x in (self.same_work,self.branch,self.unrelated,self.confidence):
   if not 0<=float(x)<=1:raise ValueError("assessment values must be 0..1")
 def to_dict(self):return asdict(self)
