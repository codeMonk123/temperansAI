import time
class RetryProvider:
    def __init__(self,provider,retries=2,backoff=(1,2),sleep_fn=time.sleep):
        self.provider=provider;self.retries=retries;self.backoff=backoff;self.sleep_fn=sleep_fn
    def assess(self,event,candidates):
        last=None
        for i in range(self.retries+1):
            try:return self.provider.assess(event,candidates)
            except Exception as e:
                last=e;text=str(e).lower()
                retryable=any(x in text for x in ("429","500","502","503","504","unavailable","high demand","timeout","overloaded"))
                if not retryable:raise
                if i<self.retries:self.sleep_fn(self.backoff[min(i,len(self.backoff)-1)])
        raise last
