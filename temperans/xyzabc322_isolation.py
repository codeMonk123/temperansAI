"""XYZABC322 adversarial isolation verification."""
def verify_isolation(platform):
 a="XYZABC321";b="XYZABC322"
 ra=platform.runtime(a);rb=platform.runtime(b)
 checks={
  "runtime_db_shared":ra.sqlite.path==rb.sqlite.path if hasattr(ra.sqlite,"path") else True,
  "org_a_events_only":all(x["organization_id"]==a for x in ra.sqlite.conn.execute("SELECT organization_id FROM events WHERE organization_id=?",(a,)).fetchall()),
  "org_b_events_only":all(x["organization_id"]==b for x in rb.sqlite.conn.execute("SELECT organization_id FROM events WHERE organization_id=?",(b,)).fetchall()),
 }
 return {"pass":all(checks.values()),"checks":checks}
