from __future__ import annotations
import json, os, time, uuid
from confluent_kafka import Producer, Consumer

BOOTSTRAP=os.getenv('KAFKA_BOOTSTRAP_SERVERS','kafka:9092'); EVENTS='streamsure.events'; CERTS='streamsure.certificates'
def send(p,obj): p.produce(EVENTS,key=obj['state_id'].encode(),value=json.dumps(obj).encode()); p.flush(10)
def main():
    p=Producer({'bootstrap.servers':BOOTSTRAP,'enable.idempotence':True,'acks':'all'})
    state='inventory-e15-'+uuid.uuid4().hex[:8]; now=int(time.time()*1000); req=['warehouse-a','warehouse-b','warehouse-c']
    send(p,{'type':'warehouse_update','state_id':state,'source':'warehouse-a','available':60,'event_time_ms':now-100,'semantic_ok':True})
    send(p,{'type':'warehouse_update','state_id':state,'source':'warehouse-b','available':47,'event_time_ms':now-100,'semantic_ok':True})
    # warehouse-c intentionally absent: same derived state evaluated for D0 and D3
    send(p,{'type':'decision','state_id':state,'decision_id':'dashboard','decision_class':0,'committed_inventory':100,'required_sources':req,'event_time_ms':now,'max_age_ms':5000,'purpose':'E15 low-consequence observation'})
    send(p,{'type':'decision','state_id':state,'decision_id':'ship-100','decision_class':3,'committed_inventory':100,'required_sources':req,'event_time_ms':now,'max_age_ms':5000,'purpose':'E15 high-consequence shipment'})
    c=Consumer({'bootstrap.servers':BOOTSTRAP,'group.id':'streamsure-smoke-'+uuid.uuid4().hex,'auto.offset.reset':'earliest'}); c.subscribe([CERTS])
    found={}; deadline=time.time()+45
    while time.time()<deadline and len(found)<2:
        m=c.poll(1)
        if m is None or m.error(): continue
        e=json.loads(m.value()); cert=e['certificate']
        if cert.get('state_id')==state: found[cert['decision_id']]=cert
    c.close()
    print(json.dumps({'state_id':state,'certificates':found},indent=2))
    assert found.get('dashboard',{}).get('outcome')=='CERTIFIED', found
    assert found.get('ship-100',{}).get('outcome')=='WAIT', found
    assert found['dashboard']['state_id']==found['ship-100']['state_id']==state, found
    print('PHASE4_E15_DISTRIBUTED_SMOKE=PASS')
if __name__=='__main__': main()
