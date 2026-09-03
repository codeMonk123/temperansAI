from temperans.platform import TemperansPlatform
from temperans.runtime_support import with_concurrency_retry
from temperans.sqlite_store import ConcurrentTrajectoryUpdate

def test_observe_returns_and_persists_l1_signals(tmp_path):
 p=TemperansPlatform(tmp_path/"p");c=p.create_organization(organization_id="o",name="o")
 r=p.observe_with_key(api_key=c["api_key"],payload={"event_id":"e","workspace_id":"w","external_user_id":"u","surface":"chat","conversation_id":"c","content":{"text":"Ticket PROD-218 failed"}})
 assert r["signals"] and all(x["maturity"]=="L1" for x in r["signals"])
 assert r["instrumentation"]["trajectory_version"]>=1
 assert len(p.runtime("o").signal_support.store.list())==len(r["signals"])

def test_duplicate_event_does_not_duplicate_signals(tmp_path):
 p=TemperansPlatform(tmp_path/"p");c=p.create_organization(organization_id="o",name="o")
 x={"event_id":"e","workspace_id":"w","external_user_id":"u","surface":"chat","conversation_id":"c","content":{"text":"Ticket PROD-218 failed"}}
 a=p.observe_with_key(api_key=c["api_key"],payload=x);n=len(p.runtime("o").signal_support.store.list())
 b=p.observe_with_key(api_key=c["api_key"],payload=x)
 assert a==b and len(p.runtime("o").signal_support.store.list())==n

def test_bounded_concurrency_retry():
 calls={"n":0,"reload":0}
 def fn():
  calls["n"]+=1
  if calls["n"]==1:raise ConcurrentTrajectoryUpdate("stale")
  return "ok"
 def reload():calls["reload"]+=1
 assert with_concurrency_retry(fn,reload,max_retries=1)=="ok"
 assert calls=={"n":2,"reload":1}
