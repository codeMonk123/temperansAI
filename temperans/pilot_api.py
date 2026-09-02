import json,os
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse,parse_qs
from temperans.pilot_service import PilotService

S=PilotService(os.environ.get("TEMPERANS_PILOT_DATA",".temperans/pilot"))
HTML="""<!doctype html><meta charset=utf-8><title>Temperans Pilot</title>
<style>body{font-family:system-ui;max-width:900px;margin:40px auto;padding:0 20px}.card{border:1px solid #ddd;border-radius:12px;padding:16px;margin:12px 0}input,textarea,button{font:inherit;padding:8px;margin:4px}textarea{width:90%;height:70px}pre{white-space:pre-wrap;background:#f5f5f5;padding:10px}</style>
<h1>Temperans Pilot V1</h1><p>Persistent cross-surface work trajectories</p>
<div class=card><input id=w value=startup_x><input id=p value=person_001><button onclick=load()>Load trajectories</button></div>
<div class=card><input id=s value=slack><input id=c value=conv_1><br><input id=g value="restore stable production deployment" size=55><br><textarea id=x>production deployment is failing</textarea><br><button onclick=observe()>Observe</button><pre id=r></pre></div>
<div id=list></div>
<script>
async function req(u,o){let r=await fetch(u,o);return r.json()} const q=x=>document.getElementById(x);
async function load(){let d=await req('/api/trajectories?workspace_id='+encodeURIComponent(q('w').value)+'&person_id='+encodeURIComponent(q('p').value));q('list').innerHTML=(d.trajectories||[]).map(t=>'<div class=card><b>'+t.goal+'</b> — '+t.lifecycle+'<br>'+t.current_state+'<br><small>'+(t.surfaces||[]).join(' → ')+'</small></div>').join('')}
async function observe(){let d=await req('/api/observe',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({workspace_id:q('w').value,person_id:q('p').value,conversation_id:q('c').value,surface:q('s').value,goal:q('g').value,current_problem:q('x').value})});q('r').textContent=JSON.stringify(d,null,2);load()} load();
</script>"""

class H(BaseHTTPRequestHandler):
    def j(self,n,x):
        b=json.dumps(x,default=str).encode(); self.send_response(n); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)
    def body(self):
        n=int(self.headers.get("Content-Length","0")); return json.loads(self.rfile.read(n) or b"{}")
    def do_GET(self):
        u=urlparse(self.path); q=parse_qs(u.query)
        if u.path=="/":
            b=HTML.encode(); self.send_response(200); self.send_header("Content-Type","text/html"); self.send_header("Content-Length",str(len(b))); self.end_headers(); return self.wfile.write(b)
        if u.path=="/api/health": return self.j(200,{"status":"ok","linker":"temperans-linker-v0.1"})
        if u.path=="/api/trajectories": return self.j(200,{"trajectories":S.trajectories(q.get("workspace_id",[""])[0],q.get("person_id",[""])[0])})
        if u.path=="/api/trajectory":
            x=S.trajectory(q.get("id",[""])[0]); return self.j(200 if x else 404,x or {"error":"not found"})
        if u.path=="/api/corrections": return self.j(200,{"corrections":S.corrections()})
        return self.j(404,{"error":"not found"})
    def do_POST(self):
        try:
            x=self.body()
            if self.path=="/api/observe": return self.j(200,S.observe(x))
            if self.path=="/api/correct": return self.j(200,S.correct(x))
            if self.path=="/api/identity/link": return self.j(200,S.link_identity(x))
            return self.j(404,{"error":"not found"})
        except Exception as e: return self.j(400,{"error":type(e).__name__,"message":str(e)})
    def log_message(self,*a): pass

def main():
    host=os.environ.get("TEMPERANS_HOST","127.0.0.1"); port=int(os.environ.get("TEMPERANS_PORT","8765"))
    print(f"Temperans Pilot V1: http://{host}:{port}")
    ThreadingHTTPServer((host,port),H).serve_forever()
if __name__=="__main__": main()
