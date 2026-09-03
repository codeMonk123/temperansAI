from temperans.provider_resilience import ResilientFrontierProvider
from temperans.frontier_assessment import FrontierAssessment

class Fails:
 def __init__(self,msg):self.msg=msg;self.n=0
 def assess(self,e,c):self.n+=1;raise RuntimeError(self.msg)
class Works:
 def __init__(self):self.n=0
 def assess(self,e,c):
  self.n+=1;return FrontierAssessment("new",None,.9),{"tokens":1}

def test_retries_then_falls_back():
 a=Fails("Kimi HTTP 429: engine_overloaded");b=Works()
 r,u=ResilientFrontierProvider([("kimi",a),("gemini",b)],max_retries=1,sleep_fn=lambda _:None).assess({},[])
 assert not r.unavailable and r.provider=="gemini" and r.assessment.action=="new"
 assert a.n==2 and b.n==1

def test_all_unavailable_returns_safe_result():
 a=Fails("HTTP 503 unavailable");b=Fails("HTTP 429 high demand")
 r,_=ResilientFrontierProvider([("a",a),("b",b)],max_retries=0,sleep_fn=lambda _:None).assess({},[])
 assert r.unavailable and r.assessment is None

def test_fatal_provider_error_falls_through_without_retry():
 a=Fails("invalid schema");b=Works()
 r,_=ResilientFrontierProvider([("a",a),("b",b)],max_retries=3,sleep_fn=lambda _:None).assess({},[])
 assert a.n==1 and r.provider=="b"
