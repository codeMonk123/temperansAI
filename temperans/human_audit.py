"""Frozen human-audit export/scoring contract."""
import json,hashlib
def build_audit_sample(rows,n=20):
 # deterministic: sort by event_id, take first N; never sample after seeing labels.
 sample=sorted(rows,key=lambda x:str(x.get("event_id","")))[:n]
 canonical=json.dumps(sample,sort_keys=True,separators=(",",":"),default=str)
 return {"audit_version":"v1","sample_size":len(sample),
         "sample_sha256":hashlib.sha256(canonical.encode()).hexdigest(),
         "rows":[{"audit_id":f"audit_{i+1:03d}","event_id":r.get("event_id"),
                  "predicted":r.get("pred"),"gold_hidden":r.get("gold"),
                  "source":r.get("source"),"human_correct":None,
                  "human_false_merge":None,"human_notes":""}
                 for i,r in enumerate(sample)]}
def score_audit(audit):
 rows=audit["rows"]
 if any(r["human_correct"] is None or r["human_false_merge"] is None for r in rows):
  return {"status":"INCOMPLETE","milestone_a_pass":False}
 correct=sum(bool(r["human_correct"]) for r in rows)
 false_merges=sum(bool(r["human_false_merge"]) for r in rows)
 rate=correct/len(rows) if rows else 0
 return {"status":"COMPLETE","sample_size":len(rows),"correct":correct,
         "correct_rate":rate,"false_merges":false_merges,
         "milestone_a_pass":rate>=.70 and false_merges==0}
