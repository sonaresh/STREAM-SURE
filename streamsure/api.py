from __future__ import annotations
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
import json, time
from dataclasses import asdict
from .models import *
from .service import StreamSureService
from . import __version__


def _state_from(d):
    ed=d.get('evidence',{})
    e=Evidence(**{k:TriState(ed.get(k,'PASS')) for k in ['temporal','contract','lineage','freshness','uncertainty','invariant','decision_policy']}, details=ed.get('details',{}))
    return DecisionBearingState(
      state_id=d['state_id'],state_version=int(d.get('state_version',1)),domain=d['domain'],value=d['value'],evidence=e,
      event_time_start=float(d.get('event_time_start',time.time()-1)),event_time_end=float(d.get('event_time_end',time.time())),
      required_sources=d.get('required_sources',[]),source_freshness=d.get('source_freshness',{}),source_completeness=d.get('source_completeness',{}),
      contract_versions=d.get('contract_versions',{}),producer_versions=d.get('producer_versions',{}),transformation_version=d.get('transformation_version','1.0'),
      lineage_reference=d.get('lineage_reference','lineage://api'),uncertainty_context=d.get('uncertainty_context',{})
    )

def _req_from(d):
    return DecisionRequest(d['decision_id'], DecisionClass(int(d.get('decision_class',2))), d.get('purpose','api'), bool(d.get('allow_provisional_fallback', False)), d.get('max_provisional_class'))

def cert_json(c):
    d=asdict(c); d['outcome']=c.outcome.value; return d

class Handler(BaseHTTPRequestHandler):
    service=None
    counters={'requests':0,'certify':0,'certify_batch':0,'repair':0,'errors':0}
    protocol_version='HTTP/1.1'
    def log_message(self, fmt, *args): pass
    def _send(self, code, obj, ctype='application/json'):
        data=(json.dumps(obj,sort_keys=True,separators=(',',':')).encode() if ctype=='application/json' else obj.encode())
        self.send_response(code); self.send_header('Content-Type',ctype); self.send_header('Content-Length',str(len(data))); self.send_header('Connection','keep-alive'); self.end_headers(); self.wfile.write(data)
    def do_GET(self):
        Handler.counters['requests']+=1; p=urlparse(self.path).path
        if p=='/health': return self._send(200,{'status':'ok','service':'STREAM-SURE','version':__version__})
        if p=='/metrics': return self._send(200,'\n'.join(f"streamsure_{k}_total {v}" for k,v in Handler.counters.items())+'\n','text/plain; version=0.0.4')
        if p.startswith('/certificates/'):
            c=self.service.store.get_certificate(p.split('/')[-1]); return self._send(200,cert_json(c)) if c else self._send(404,{'error':'not_found'})
        return self._send(404,{'error':'not_found'})
    def do_POST(self):
        Handler.counters['requests']+=1
        try:
            n=int(self.headers.get('Content-Length','0')); d=json.loads(self.rfile.read(n) or b'{}')
            if self.path=='/certify':
                Handler.counters['certify']+=1
                return self._send(200,cert_json(self.service.certify(_state_from(d['state']),_req_from(d['decision']))))
            if self.path=='/certify-batch':
                items=d.get('items',[])
                if not isinstance(items,list) or not items or len(items)>512: raise ValueError('items must contain 1..512 certification requests')
                Handler.counters['certify']+=len(items); Handler.counters['certify_batch']+=1
                pairs=[(_state_from(x['state']),_req_from(x['decision'])) for x in items]
                return self._send(200,{'certificates':[cert_json(c) for c in self.service.certify_batch(pairs)]})
            if self.path=='/repair':
                Handler.counters['repair']+=1
                c,affected=self.service.repair(d['old_certificate_id'],_state_from(d['state']),_req_from(d['decision']))
                return self._send(200,{'certificate':cert_json(c),'affected_decisions':affected})
            return self._send(404,{'error':'not_found'})
        except Exception as e:
            Handler.counters['errors']+=1; return self._send(400,{'error':type(e).__name__,'message':str(e)})

def serve(host='127.0.0.1',port=8080,db_path='evidence/streamsure.db'):
    Handler.service=StreamSureService(db_path); server=ThreadingHTTPServer((host,port),Handler); server.daemon_threads=True
    print(f"STREAM-SURE API listening on http://{host}:{port}")
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally:
        server.shutdown(); server.server_close(); Handler.service.close(); Handler.service=None
