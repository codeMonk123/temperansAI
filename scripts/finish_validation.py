#!/usr/bin/env python3
import argparse,json,hashlib,tempfile,subprocess,sys
from collections import Counter,defaultdict
from pathlib import Path
from temperans.platform import TemperansPlatform
from temperans.xyzabc321_dataset import build_xyzabc321
from temperans.xyzabc321_identity import link_xyzabc321_identities

def clean(e):
 x=dict(e)
 for k in ("_gold_trajectory","_gold_work","_gold_relation"):x.pop(k,None)
 return x

def diagnose():
 with tempfile.TemporaryDirectory() as d:
  p=TemperansPlatform(d);p.create_organization(organization_id="XYZABC321",name="XYZABC321")
  rt=p.runtime("XYZABC321");link_xyzabc321_identities(rt);events,_=build_xyzabc321()
  rows=[]
  for e in events:
   r=rt.observe(clean(e));rows.append((e,r))
 clar=[(e,r) for e,r in rows if r["decision"]=="clarify"];src=Counter(r.get("source") for _,r in clar);rules=Counter()
 for _,r in clar:
  for x in (r.get("trace") or {}).get("rules",[]):rules[x.get("rule","unknown")]+=1
 report={"events":len(rows),"clarifications":len(clar),"coverage":(len(rows)-len(clar))/len(rows),
 "clarify_by_source":dict(src),"clarify_rules":dict(rules),
 "examples":[{"event_id":e["event_id"],"gold":e["_gold_trajectory"],"source":r.get("source"),
 "rules":(r.get("trace") or {}).get("rules",[])} for e,r in clar]}
 Path("xyzabc321_clarify_diagnostic.json").write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!="examples"},indent=2))

def verify():
 q=subprocess.run([sys.executable,"-m","pytest","-q"],capture_output=True,text=True)
 f=Path("benchmarks/xyzabc323/xyzabc323_frozen_v1.json");sf=Path("benchmarks/xyzabc323/xyzabc323_frozen_v1.sha256")
 actual=hashlib.sha256(f.read_bytes()).hexdigest() if f.exists() else None
 expected=sf.read_text().split()[0] if sf.exists() else None
 print(json.dumps({"pytest_pass":q.returncode==0,"pytest_summary":q.stdout.strip().splitlines()[-1] if q.stdout.strip() else "",
 "xyzabc323_sha_match":bool(actual and expected and actual==expected),"actual_sha256":actual,"expected_sha256":expected},indent=2))

def heldout():
 f=Path("benchmarks/xyzabc323/xyzabc323_frozen_v1.json");out=Path("xyzabc323_one_shot_result.json")
 if out.exists():raise SystemExit("ONE-SHOT RESULT ALREADY EXISTS; refusing rerun")
 events=json.loads(f.read_text());sha=hashlib.sha256(f.read_bytes()).hexdigest()
 with tempfile.TemporaryDirectory() as d:
  p=TemperansPlatform(d);p.create_organization(organization_id="XYZABC323",name="XYZABC323");rt=p.runtime("XYZABC323")
  rows=[];gold_tid={};tid_gold=defaultdict(set)
  for e in events:
   r=rt.observe(clean(e));rel=e["_gold_relation"];w=e["_gold_work"];tid=r.get("trajectory_id")
   if rel in ("clarify","ambiguous_cross_person"):ok=r["decision"]=="clarify"
   elif rel=="new":
    ok=r["decision"]=="new"
    if ok and tid:gold_tid[w]=tid
   elif rel=="attach":ok=r["decision"]=="attach" and gold_tid.get(w)==tid
   else:ok=False
   if r["decision"]!="clarify" and tid:tid_gold[tid].add(w)
   rows.append({"event_id":e["event_id"],"gold_work":w,"gold_relation":rel,"decision":r["decision"],"trajectory_id":tid,"correct":ok})
  false_merges=sum(len(v)>1 for v in tid_gold.values());by=defaultdict(list)
  for r in rows:by[r["gold_work"]].append(r)
  ev={w:xs for w,xs in by.items() if not all(x["gold_relation"] in ("clarify","ambiguous_cross_person") for x in xs)}
  good=sum(all(x["correct"] for x in xs) for xs in ev.values());rate=good/len(ev) if ev else 0
  report={"benchmark":"XYZABC323-heldout-v1","frozen_sha256":sha,"events":len(rows),"evaluable_work_trajectories":len(ev),
  "correctly_reconstructed_trajectories":good,"trajectory_reconstruction_rate":rate,"false_merge_trajectories":false_merges,
  "event_accuracy":sum(r["correct"] for r in rows)/len(rows),"milestone_a_machine_gate":rate>=.70 and false_merges==0,
  "human_audit_required":True,"rows":rows}
  out.write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!="rows"},indent=2))

if __name__=="__main__":
 a=argparse.ArgumentParser();a.add_argument("command",choices=["diagnose","verify","heldout"]);x=a.parse_args()
 {"diagnose":diagnose,"verify":verify,"heldout":heldout}[x.command]()
