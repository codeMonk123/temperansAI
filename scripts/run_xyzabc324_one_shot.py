#!/usr/bin/env python3
"""FINAL HELD-OUT launcher. Refuses repeat. Run only after development + regression are green."""
import hashlib,json,subprocess,sys
from pathlib import Path
f=Path("benchmarks/xyzabc324/xyzabc324_frozen_v1.json");sf=Path("benchmarks/xyzabc324/xyzabc324_frozen_v1.sha256")
sentinel=Path("xyzabc324_FINAL_CONSUMED.json")
if sentinel.exists():raise SystemExit("XYZABC324 ALREADY CONSUMED; refusing rerun")
actual=hashlib.sha256(f.read_bytes()).hexdigest();expected=sf.read_text().split()[0]
if actual!=expected:raise SystemExit("XYZABC324 SHA MISMATCH")
q=subprocess.run([sys.executable,"-m","pytest","-q"])
if q.returncode:raise SystemExit("pytest failed; held-out not consumed")
# Consumption marker only. Evaluation implementation must be frozen/reviewed before
# scoring; this script intentionally refuses to improvise scoring after seeing data.
sentinel.write_text(json.dumps({"frozen_sha256":actual,"status":"CONSUMED_FOR_FINAL_EVALUATION"},indent=2))
print(json.dumps({"xyzabc324_sha256":actual,"pytest_pass":True,"status":"CONSUMED_FOR_FINAL_EVALUATION"},indent=2))
