"""Provider resilience for L2 frontier intelligence.
Transient model outages never fail deterministic Temperans ingestion.
"""
from dataclasses import dataclass,field
import time

@dataclass(frozen=True)
class ProviderAttempt:
 provider:str
 status:str
 detail:str=""
 attempt:int=1

@dataclass(frozen=True)
class ResilientAssessment:
 assessment:object|None
 provider:str|None
 unavailable:bool
 attempts:list=field(default_factory=list)

class ResilientFrontierProvider:
 def __init__(self,providers,max_retries=2,backoff=(1.0,2.0),sleep_fn=time.sleep):
  self.providers=list(providers);self.max_retries=max_retries
  self.backoff=tuple(backoff);self.sleep_fn=sleep_fn
 def _retryable(self,exc):
  text=str(exc).lower()
  return any(x in text for x in ("http 429","http 500","http 502","http 503","http 504",
                                  "engine_overloaded","high demand","unavailable","timeout"))
 def assess(self,event,candidates):
  attempts=[]
  for name,provider in self.providers:
   for n in range(self.max_retries+1):
    try:
     assessment,usage=provider.assess(event,candidates)
     attempts.append(ProviderAttempt(name,"success",attempt=n+1))
     return ResilientAssessment(assessment,name,False,attempts),usage
    except Exception as exc:
     retryable=self._retryable(exc)
     attempts.append(ProviderAttempt(name,"retryable_error" if retryable else "fatal_error",
                                     str(exc)[:500],n+1))
     if not retryable:break
     if n<self.max_retries:
      delay=self.backoff[min(n,len(self.backoff)-1)] if self.backoff else 0
      self.sleep_fn(delay)
  return ResilientAssessment(None,None,True,attempts),{}
