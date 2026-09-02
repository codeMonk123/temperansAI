import shutil
from pathlib import Path
from temperans.pilot_service import PilotService
root=Path(".temperans/pilot-smoke")
if root.exists(): shutil.rmtree(root)
s=PilotService(root)
a=s.observe({"workspace_id":"w","person_id":"u","conversation_id":"c1","surface":"slack",
             "goal":"restore production deployment","current_problem":"Email ops@example.com; PROD-218 deployment fails"})
b=s.observe({"workspace_id":"w","person_id":"u","conversation_id":"c2","surface":"chatbot",
             "goal":"restore production deployment","current_problem":"Update PROD-218: service starts"})
assert a["decision"]=="new"
assert b["decision"]=="attach"
assert a["trajectory_id"]==b["trajectory_id"]
assert "[REDACTED_EMAIL]" in s.store.read("events.jsonl")[0]["current_problem"]
cor=s.correct({"decision_record_id":b["decision_record_id"],"workspace_id":"w","person_id":"u",
               "conversation_id":"c2","original_trajectory_id":b["trajectory_id"],
               "action":"confirm","target_trajectory_id":b["trajectory_id"]})
assert cor["action"]=="confirm"
assert len(s.store.read("events.jsonl"))==2
assert len(s.store.read("decisions.jsonl"))==2
assert len(s.store.read("corrections.jsonl"))==1
print("PILOT V1 SMOKE: PASS")
print("trajectory:",a["trajectory_id"])
print("events:",len(s.store.read("events.jsonl")))
print("decisions:",len(s.store.read("decisions.jsonl")))
print("corrections:",len(s.store.read("corrections.jsonl")))
