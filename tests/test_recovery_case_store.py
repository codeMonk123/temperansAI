from temperans.sqlite_store import SQLiteStore
from temperans.recovery_case_store import RecoveryCaseStore
def test_cases_persist_and_order(tmp_path):
 s=SQLiteStore(tmp_path/"x.db");r=RecoveryCaseStore(s)
 r.put("o","b","e2",2,{"x":2},[],None,None);r.put("o","a","e1",1,{"x":1},[],None,None)
 assert [x["event_id"] for x in r.rows("o")]==["e1","e2"]
 s.close();s=SQLiteStore(tmp_path/"x.db");assert len(RecoveryCaseStore(s).rows("o"))==2
