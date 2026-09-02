import json,os
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse,parse_qs
from temperans.platform import TemperansPlatform
from temperans.idempotency import IdempotencyConflict
P=TemperansPlatform(os.environ.get('TEMPERANS_PLATFORM_DATA','.temperans/platform'))
MAX=int(os.environ.get('TEMPERANS_MAX_BODY_BYTES','262144'))
class H(BaseHTTPRequestHandler):
    def j(self,n,x):
        b=json.dumps(x,default=str).encode(); self.send_response(n); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
    def auth(self):
        h=self.headers.get('Authorization','')
        if not h.startswith('Bearer '):return None,None
        k=h[7:].strip(); return P.authenticate(k),k
    def body(self):
        n=int(self.headers.get('Content-Length','0'))
        if n>MAX:raise ValueError('request too large')
        return json.loads(self.rfile.read(n) or b'{}')
    def do_GET(self):
        u=urlparse(self.path)
        if u.path=='/health':return self.j(200,{'status':'ok'})
        cfg,key=self.auth()
        if not cfg:return self.j(401,{'error':'unauthorized'})
        r=P.runtime(cfg.organization_id); q=parse_qs(u.query)
        if u.path=='/v1/trajectories':return self.j(200,{'organization_id':cfg.organization_id,'trajectories':r.service.trajectories(q.get('workspace_id',[''])[0],q.get('person_id',[''])[0])})
        if u.path=='/v1/trajectory':
            x=r.service.trajectory(q.get('id',[''])[0]); return self.j(200 if x else 404,x or {'error':'not_found'})
        if u.path=='/v1/corrections':return self.j(200,{'organization_id':cfg.organization_id,'corrections':r.service.corrections()})
        return self.j(404,{'error':'not_found'})
    def do_POST(self):
        cfg,key=self.auth()
        if not cfg:return self.j(401,{'error':'unauthorized'})
        try:
            x=self.body(); r=P.runtime(cfg.organization_id)
            if self.path=='/v1/observe':return self.j(200,P.observe_with_key(api_key=key,payload=x))
            if self.path=='/v1/correct':return self.j(200,r.service.correct(x))
            if self.path=='/v1/identity/link':return self.j(200,r.link_identity(workspace_id=x['workspace_id'],surface=x['surface'],external_user_id=x['external_user_id'],person_id=x['person_id']))
            return self.j(404,{'error':'not_found'})
        except IdempotencyConflict:return self.j(409,{'error':'idempotency_conflict'})
        except PermissionError:return self.j(403,{'error':'forbidden'})
        except ValueError:return self.j(400,{'error':'invalid_request'})
        except Exception:return self.j(500,{'error':'internal_error'})
    def log_message(self,*a):pass
def main():
    host=os.environ.get('TEMPERANS_HOST','127.0.0.1'); port=int(os.environ.get('TEMPERANS_PORT','8766'))
    print(f'Temperans Partner API: http://{host}:{port}'); ThreadingHTTPServer((host,port),H).serve_forever()
if __name__=='__main__':main()
