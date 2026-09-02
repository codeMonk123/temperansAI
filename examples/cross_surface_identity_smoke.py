import json,os,subprocess,tempfile,time
from urllib.request import Request,urlopen
from temperans.surface_client import SurfaceClient
def post(url,x):
    r=Request(url,data=json.dumps(x).encode(),method="POST",headers={"Content-Type":"application/json"})
    with urlopen(r,timeout=3) as z:return json.loads(z.read())
with tempfile.TemporaryDirectory() as root:
    env=dict(os.environ); env["TEMPERANS_PILOT_DATA"]=root; env["TEMPERANS_PORT"]="8892"
    proc=subprocess.Popen(["python","-m","temperans.pilot_api"],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        for _ in range(40):
            try:
                with urlopen("http://127.0.0.1:8892/api/health",timeout=.5): break
            except Exception: time.sleep(.1)
        base="http://127.0.0.1:8892"
        post(base+"/api/identity/link",{"workspace_id":"acme","surface":"slack","external_user_id":"U12345","person_id":"person_001"})
        post(base+"/api/identity/link",{"workspace_id":"acme","surface":"acme_bot","external_user_id":"user_872","person_id":"person_001"})
        slack=SurfaceClient("acme","slack",base); bot=SurfaceClient("acme","acme_bot",base)
        a=slack.observe("U12345","slack_1","Ticket PROD-218 deployment is failing","restore production deployment")
        b=bot.observe("user_872","bot_1","Update PROD-218: startup still fails","restore production deployment")
        assert a["trajectory_id"]==b["trajectory_id"] and b["decision"]=="attach"
        with urlopen(base+"/api/trajectories?workspace_id=acme&person_id=person_001") as r: rows=json.loads(r.read())["trajectories"]
        assert len(rows)==1 and {"slack","acme_bot"}.issubset(set(rows[0]["surfaces"]))
        print("CROSS-SURFACE IDENTITY: PASS")
        print("trajectory:",a["trajectory_id"]); print("surfaces:",rows[0]["surfaces"])
    finally:
        proc.terminate()
        try:proc.wait(timeout=3)
        except Exception:proc.kill()
