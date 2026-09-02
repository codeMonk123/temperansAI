import shutil
from pathlib import Path
from temperans.pilot_service import PilotService
root=Path(".temperans/restart-smoke")
if root.exists(): shutil.rmtree(root)
a=PilotService(root)
r1=a.observe({"workspace_id":"w","person_id":"u","conversation_id":"c1","surface":"slack","goal":"restore deployment","current_problem":"PROD-218 deployment fails"})
tid=r1["trajectory_id"]
b=PilotService(root)
assert tid in b.runtime.trajectories
r2=b.observe({"workspace_id":"w","person_id":"u","conversation_id":"c2","surface":"chatbot","goal":"restore deployment","current_problem":"Update PROD-218 service starts"})
assert r2["trajectory_id"]==tid and r2["decision"]=="attach"
print("PILOT RESTART SMOKE: PASS",tid)
