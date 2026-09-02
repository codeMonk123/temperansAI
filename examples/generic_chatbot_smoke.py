import json,os,subprocess,tempfile,time
from urllib.request import urlopen
from temperans.chatbot import TemperansChatbot

with tempfile.TemporaryDirectory() as root:
    env=dict(os.environ); env["TEMPERANS_PILOT_DATA"]=root; env["TEMPERANS_PORT"]="8891"
    proc=subprocess.Popen(["python","-m","temperans.pilot_api"],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        for _ in range(40):
            try:
                with urlopen("http://127.0.0.1:8891/api/health",timeout=.5) as r: json.loads(r.read()); break
            except Exception: time.sleep(.1)
        else: raise RuntimeError("pilot API did not start")
        bot=TemperansChatbot("acme","acme_bot","http://127.0.0.1:8891")
        a=bot.before_reply("person_001","bot_1","Ticket PROD-218 deployment is failing","restore production deployment")
        b=bot.before_reply("person_001","bot_2","Update PROD-218: service starts now","restore production deployment")
        assert a["trajectory_id"]==b["trajectory_id"]
        assert b["decision"]=="attach"
        assert "restore production deployment" in bot.context_text(b)
        rows=bot.client.trajectories("acme","person_001")["trajectories"]
        assert len(rows)==1
        print("GENERIC CHATBOT SMOKE: PASS")
        print("trajectory:",b["trajectory_id"])
        print("decision:",b["decision"])
    finally:
        proc.terminate()
        try: proc.wait(timeout=3)
        except Exception: proc.kill()
