from temperans.human_audit import build_audit_sample,score_audit
def test_audit_sample_is_deterministic():
 rows=[{"event_id":str(i),"pred":"x","gold":"y","source":"s"} for i in range(30,0,-1)]
 a=build_audit_sample(rows,20);b=build_audit_sample(rows,20)
 assert a["sample_sha256"]==b["sample_sha256"] and len(a["rows"])==20
def test_audit_gate_is_not_faked():
 a=build_audit_sample([{"event_id":"e","pred":"x","gold":"y","source":"s"}],1)
 assert score_audit(a)["status"]=="INCOMPLETE"
 a["rows"][0]["human_correct"]=True;a["rows"][0]["human_false_merge"]=False
 assert score_audit(a)["milestone_a_pass"] is True
def test_false_merge_blocks_pass():
 a=build_audit_sample([{"event_id":"e","pred":"x","gold":"y","source":"s"}],1)
 a["rows"][0]["human_correct"]=True;a["rows"][0]["human_false_merge"]=True
 assert score_audit(a)["milestone_a_pass"] is False
