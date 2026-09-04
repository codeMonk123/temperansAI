#!/usr/bin/env python3
"""Zero-API cache status/replay-readiness report."""
import os,json
from pathlib import Path
from temperans.sqlite_store import SQLiteStore
from temperans.adjudication_cache import AdjudicationCache
from temperans.recovery_case_store import RecoveryCaseStore
from temperans.cached_consensus import cached_new_consensus
DB=Path(os.environ.get("TEMPERANS_ADJUDICATION_DB",".temperans/xyzabc321_adjudication.db"))
s=SQLiteStore(DB);c=AdjudicationCache(s);r=RecoveryCaseStore(s);rows=r.rows("XYZABC321")
accepted=pending=0;reasons={}
for x in rows:
 d=cached_new_consensus(*c.pair("XYZABC321",x["case_id"]))
 accepted+=int(d["accepted"]);pending+=int(c.get("XYZABC321",x["case_id"],"verifier") is None)
 reasons[d["reason"]]=reasons.get(d["reason"],0)+1
print(json.dumps({"cases":len(rows),"cached_consensus_new":accepted,
 "pending_verifier":pending,"reasons":reasons,
 "zero_api":True},indent=2))
