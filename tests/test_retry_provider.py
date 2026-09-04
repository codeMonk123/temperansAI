import pytest
from temperans.retry_provider import RetryProvider
class P:
    def __init__(self,n):self.n=n;self.calls=0
    def assess(self,e,c):
        self.calls+=1
        if self.calls<=self.n:raise RuntimeError("HTTP 503 unavailable")
        return "ok",{}
def test_retry_recovers():
    p=P(2);r=RetryProvider(p,retries=2,sleep_fn=lambda _:None)
    assert r.assess({},[])[0]=="ok" and p.calls==3
def test_nonretryable_fails():
    class X:
        def assess(self,e,c):raise RuntimeError("invalid schema")
    with pytest.raises(RuntimeError,match="invalid schema"):
        RetryProvider(X(),retries=5,sleep_fn=lambda _:None).assess({},[])
