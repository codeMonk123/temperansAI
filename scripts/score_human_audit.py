import json,sys
from pathlib import Path
from temperans.human_audit import score_audit
path=Path(sys.argv[1] if len(sys.argv)>1 else "xyzabc321_human_audit_v1.json")
audit=json.loads(path.read_text());result=score_audit(audit)
print(json.dumps(result,indent=2))
