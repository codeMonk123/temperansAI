from temperans.adjudication_cache import recovery_case_id,AdjudicationCache
from temperans.cached_consensus import cached_new_consensus
from temperans.sqlite_store import SQLiteStore
def test_case_id_stable():
 e={"x":1};c=[{"trajectory_id":"t"}]
 assert recovery_case_id(e,c)==recovery_case_id(e,c)
def test_cache_survives_reopen(tmp_path):
 s=SQLiteStore(tmp_path/"x.db");c=AdjudicationCache(s)
 c.put("o","rc","primary","m",{"action":"new","candidate_id":None,"confidence":.9})
 s.close();s=SQLiteStore(tmp_path/"x.db");c=AdjudicationCache(s)
 assert c.get("o","rc","primary")["assessment"]["action"]=="new"
def test_consensus_requires_both(tmp_path):
 s=SQLiteStore(tmp_path/"x.db");c=AdjudicationCache(s)
 c.put("o","rc","primary","k3",{"action":"new","candidate_id":None,"confidence":.9})
 assert not cached_new_consensus(*c.pair("o","rc"))["accepted"]
 c.put("o","rc","verifier","gemini",{"action":"new","candidate_id":None,"confidence":.9})
 assert cached_new_consensus(*c.pair("o","rc"))["accepted"]
