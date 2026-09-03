from dataclasses import dataclass,field
@dataclass
class PerceptionRequest:
    event:dict
    candidate_views:list[dict]=field(default_factory=list)
@dataclass
class PerceptionResult:
    provider:str; model:str; adapter_version:str
    signals:list=field(default_factory=list); raw_metadata:dict=field(default_factory=dict)
class PerceptionProvider:
    def perceive(self,request:PerceptionRequest)->PerceptionResult:raise NotImplementedError
