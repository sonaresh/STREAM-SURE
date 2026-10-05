from __future__ import annotations
import http.client, json, os, signal, time
from urllib.parse import urlsplit
from confluent_kafka import Consumer, Producer, KafkaError

BOOTSTRAP=os.getenv('KAFKA_BOOTSTRAP_SERVERS','kafka:9092')
IN_TOPIC=os.getenv('STREAMSURE_REQUEST_TOPIC','streamsure.certify.requests')
OUT_TOPIC=os.getenv('STREAMSURE_CERT_TOPIC','streamsure.certificates')
API=os.getenv('STREAMSURE_BATCH_API','http://streamsure:8080/certify-batch')
BATCH_SIZE=int(os.getenv('STREAMSURE_BRIDGE_BATCH_SIZE','64'))
BATCH_WAIT=float(os.getenv('STREAMSURE_BRIDGE_BATCH_WAIT_SEC','0.02'))
RUN=True

class PersistentJSONClient:
    def __init__(self,url):
        u=urlsplit(url); self.host=u.hostname; self.port=u.port or (443 if u.scheme=='https' else 80); self.path=u.path or '/'; self.https=u.scheme=='https'; self.conn=None
    def _new(self):
        cls=http.client.HTTPSConnection if self.https else http.client.HTTPConnection
        self.conn=cls(self.host,self.port,timeout=15)
    def post(self,obj):
        body=json.dumps(obj,separators=(',',':')).encode()
        for attempt in range(2):
            try:
                if self.conn is None: self._new()
                self.conn.request('POST',self.path,body=body,headers={'Content-Type':'application/json','Content-Length':str(len(body)),'Connection':'keep-alive'})
                r=self.conn.getresponse(); raw=r.read()
                if r.status!=200: raise RuntimeError(f'HTTP {r.status}: {raw[:300]!r}')
                return json.loads(raw)
            except (OSError,http.client.HTTPException):
                try:
                    if self.conn: self.conn.close()
                except Exception: pass
                self.conn=None
                if attempt: raise
    def close(self):
        if self.conn:
            try:self.conn.close()
            except Exception:pass
            self.conn=None

def main():
    global RUN
    signal.signal(signal.SIGTERM,lambda *_:globals().__setitem__('RUN',False)); signal.signal(signal.SIGINT,lambda *_:globals().__setitem__('RUN',False))
    c=Consumer({
        'bootstrap.servers':BOOTSTRAP,
        'group.id':'streamsure-certification-bridge-v141',
        'auto.offset.reset':'earliest',
        'enable.auto.commit':False,
        'fetch.min.bytes':1,
        'fetch.wait.max.ms':20,
        'max.poll.interval.ms':300000,
    })
    p=Producer({
        'bootstrap.servers':BOOTSTRAP,'enable.idempotence':True,'acks':'all',
        'linger.ms':5,'batch.num.messages':10000,'compression.type':'lz4',
        'queue.buffering.max.messages':1000000,
    })
    client=PersistentJSONClient(API); c.subscribe([IN_TOPIC])
    print(f'Optimized Kafka bridge: {IN_TOPIC} -> batch[{BATCH_SIZE}] {API} -> {OUT_TOPIC}',flush=True)
    try:
        while RUN:
            msgs=c.consume(num_messages=BATCH_SIZE,timeout=BATCH_WAIT)
            if not msgs: continue
            good=[]
            for m in msgs:
                if m is None: continue
                if m.error():
                    if m.error().code()!=KafkaError._PARTITION_EOF: print(f'consumer error: {m.error()}',flush=True)
                    continue
                try: good.append((m,json.loads(m.value())))
                except Exception as e: print(f'bridge decode error: {e}',flush=True)
            if not good: continue
            try:
                resp=client.post({'items':[req for _,req in good]}); certs=resp.get('certificates',[])
                if len(certs)!=len(good): raise RuntimeError(f'batch response length {len(certs)} != requests {len(good)}')
                bt=time.time()
                for (m,req),cert in zip(good,certs):
                    envelope={'request':req,'certificate':cert,'bridge_time':bt}
                    p.produce(OUT_TOPIC,key=cert.get('state_id','').encode(),value=json.dumps(envelope,separators=(',',':')).encode())
                p.flush(10)
                # commit the highest offsets returned by this poll after output delivery
                c.commit(asynchronous=False)
            except Exception as e:
                print(f'bridge batch error: {type(e).__name__}: {e}',flush=True); time.sleep(0.05)
    finally:
        client.close(); c.close(); p.flush(10)
if __name__=='__main__': main()
