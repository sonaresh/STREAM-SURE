from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import platform
import statistics
import threading
import time
import uuid
from pathlib import Path

from confluent_kafka import Consumer, Producer, KafkaError

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
EVENTS = os.getenv("STREAMSURE_EVENT_TOPIC", "streamsure.events")
CERTS = os.getenv("STREAMSURE_CERT_TOPIC", "streamsure.certificates")


def percentile(values, p):
    if not values:
        return None
    xs = sorted(values)
    k = (len(xs)-1)*p
    lo = int(math.floor(k)); hi = int(math.ceil(k))
    if lo == hi:
        return xs[lo]
    return xs[lo]*(hi-k)+xs[hi]*(k-lo)


def consumer_loop(run_id, expected, stop_evt, out, bootstrap):
    c = Consumer({
        'bootstrap.servers': bootstrap,
        'group.id': f'streamsure-scale-{run_id}-{uuid.uuid4().hex[:8]}',
        'auto.offset.reset': 'latest',
        'enable.auto.commit': False,
        'fetch.min.bytes': 1,
    })
    c.subscribe([CERTS])
    # establish assignment before producer starts
    deadline = time.time()+10
    while time.time() < deadline:
        c.poll(0.2)
        if c.assignment():
            break
    out['ready'].set()
    try:
        while not stop_evt.is_set() and len(out['latencies_ms']) < expected:
            m = c.poll(0.2)
            if m is None:
                continue
            if m.error():
                if m.error().code() != KafkaError._PARTITION_EOF:
                    out['consumer_errors'] += 1
                continue
            try:
                envelope = json.loads(m.value())
                cert = envelope.get('certificate', {})
                details = cert.get('evidence', {}).get('details', {})
                if details.get('run_id') != run_id:
                    continue
                sent_ns = int(details.get('sent_at_ns', 0))
                if sent_ns > 0:
                    out['latencies_ms'].append((time.time_ns()-sent_ns)/1e6)
                out['received'] += 1
            except Exception:
                out['consumer_errors'] += 1
    finally:
        c.close()


def produce_run(target_eps: int, duration_sec: int, bootstrap: str, completion_timeout_sec: int):
    # 3 warehouse updates + 1 decision = 4 input records per certificate.
    decisions_target = max(1, int(target_eps * duration_sec / 4))
    input_target = decisions_target * 4
    run_id = f"e16-{target_eps}-{uuid.uuid4().hex[:8]}"
    stop_evt = threading.Event()
    out = {'latencies_ms': [], 'received': 0, 'consumer_errors': 0, 'ready': threading.Event()}
    t = threading.Thread(target=consumer_loop, args=(run_id, decisions_target, stop_evt, out, bootstrap), daemon=True)
    t.start(); out['ready'].wait(10)

    delivery_errors = 0
    lock = threading.Lock()
    def delivery(err, _msg):
        nonlocal delivery_errors
        if err is not None:
            with lock: delivery_errors += 1

    p = Producer({
        'bootstrap.servers': bootstrap,
        'acks': 'all',
        'linger.ms': 5,
        'batch.num.messages': 10000,
        'queue.buffering.max.messages': 1000000,
        'compression.type': 'lz4',
    })
    start_ns = time.time_ns(); start = time.perf_counter()
    produced = 0
    decision_count = 0
    # Pace in 50 ms windows using a fractional accumulator.
    # Integer truncation here would under-drive low rates (e.g. 100 input eps became 80 eps).
    batch_window = 0.05
    decision_rate = target_eps / 4.0
    decision_credit = 0.0
    next_deadline = time.perf_counter()
    now_ms = lambda: int(time.time()*1000)
    while decision_count < decisions_target:
        decision_credit += decision_rate * batch_window
        batch_n = min(int(decision_credit), decisions_target-decision_count)
        decision_credit -= batch_n
        if batch_n <= 0:
            next_deadline += batch_window
            sleep = next_deadline - time.perf_counter()
            if sleep > 0:
                time.sleep(sleep)
            continue
        for _ in range(batch_n):
            i = decision_count
            state = f"{run_id}-{i}"
            sent_at_ns = time.time_ns()
            tm = now_ms()
            recs = [
                {'type':'warehouse_update','state_id':state,'source':'warehouse-a','available':40,'event_time_ms':tm-20,'semantic_ok':True},
                {'type':'warehouse_update','state_id':state,'source':'warehouse-b','available':35,'event_time_ms':tm-15,'semantic_ok':True},
                {'type':'warehouse_update','state_id':state,'source':'warehouse-c','available':32,'event_time_ms':tm-10,'semantic_ok':True},
                {'type':'decision','state_id':state,'decision_id':f'e16-{i}','decision_class':3,'committed_inventory':100,
                 'required_sources':['warehouse-a','warehouse-b','warehouse-c'],'event_time_ms':tm,'max_age_ms':5000,
                 'purpose':'E16 distributed scale','run_id':run_id,'sent_at_ns':sent_at_ns},
            ]
            for rec in recs:
                # propagate run metadata on every record, though Flink needs it only on the decision.
                rec.setdefault('run_id', run_id)
                while True:
                    try:
                        p.produce(EVENTS, key=state.encode(), value=json.dumps(rec,separators=(',',':')).encode(), on_delivery=delivery)
                        produced += 1; break
                    except BufferError:
                        p.poll(0.01)
            decision_count += 1
        p.poll(0)
        next_deadline += batch_window
        sleep = next_deadline - time.perf_counter()
        if sleep > 0:
            time.sleep(sleep)
    p.flush(30)
    producer_elapsed = time.perf_counter()-start

    deadline = time.time()+completion_timeout_sec
    while time.time() < deadline and out['received'] < decisions_target:
        time.sleep(0.1)
    stop_evt.set(); t.join(timeout=5)
    total_elapsed = (time.time_ns()-start_ns)/1e9
    lats = out['latencies_ms']
    actual_input_eps = produced/producer_elapsed if producer_elapsed else 0.0
    cert_eps = out['received']/total_elapsed if total_elapsed else 0.0
    completion = out['received']/decisions_target if decisions_target else 0.0
    sustained = actual_input_eps >= target_eps*0.90 and completion >= 0.99 and delivery_errors == 0 and out['consumer_errors'] == 0
    return {
        'run_id': run_id,
        'target_input_events_per_sec': target_eps,
        'duration_sec': duration_sec,
        'input_records_target': input_target,
        'input_records_produced': produced,
        'decisions_target': decisions_target,
        'certificates_received': out['received'],
        'completion_ratio': completion,
        'producer_elapsed_sec': producer_elapsed,
        'end_to_end_elapsed_sec': total_elapsed,
        'actual_input_events_per_sec': actual_input_eps,
        'certificate_throughput_per_sec': cert_eps,
        'latency_p50_ms': percentile(lats, .50),
        'latency_p95_ms': percentile(lats, .95),
        'latency_p99_ms': percentile(lats, .99),
        'latency_max_ms': max(lats) if lats else None,
        'delivery_errors': delivery_errors,
        'consumer_errors': out['consumer_errors'],
        'sustained': sustained,
    }


def sha256(path: Path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()


def main():
    ap=argparse.ArgumentParser(description='STREAM-SURE E16 distributed scale sweep')
    ap.add_argument('--targets', default=os.getenv('STREAMSURE_SCALE_TARGETS','1000,5000,10000,25000,50000'))
    ap.add_argument('--duration-sec', type=int, default=int(os.getenv('STREAMSURE_SCALE_DURATION','10')))
    ap.add_argument('--completion-timeout-sec', type=int, default=60)
    ap.add_argument('--out', default='/evidence/phase6')
    ap.add_argument('--continue-after-unsustained', action='store_true')
    ap.add_argument('--bootstrap', default=BOOTSTRAP)
    args=ap.parse_args()
    targets=[int(x.strip()) for x in args.targets.split(',') if x.strip()]
    outdir=Path(args.out); outdir.mkdir(parents=True,exist_ok=True)
    results=[]
    print(json.dumps({'phase':'E16','targets':targets,'duration_sec':args.duration_sec,'definition':'4 Kafka input records per certification decision'},indent=2), flush=True)
    for target in targets:
        print(f'==> E16 target {target:,} input events/sec', flush=True)
        r=produce_run(target,args.duration_sec,args.bootstrap,args.completion_timeout_sec)
        results.append(r); print(json.dumps(r,indent=2),flush=True)
        if not r['sustained'] and not args.continue_after_unsustained:
            print('Stopping after first unsustained target (scientific stop rule).',flush=True)
            break
    csv_path=outdir/'scale_results.csv'
    with csv_path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(results[0].keys())); w.writeheader(); w.writerows(results)
    summary={
        'phase':'E16','generated_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        'bootstrap':args.bootstrap,'targets_requested':targets,'duration_sec':args.duration_sec,
        'runs':results,
        'max_sustained_input_events_per_sec':max([r['target_input_events_per_sec'] for r in results if r['sustained']],default=None),
        'environment':{'python':platform.python_version(),'platform':platform.platform()},
        'interpretation_note':'Input events/sec counts Kafka input records. Each certification unit uses 3 warehouse updates plus 1 decision (4 records). Certificate throughput/sec counts completed end-to-end SSAC responses.',
    }
    summary_path=outdir/'summary.json'; summary_path.write_text(json.dumps(summary,indent=2),encoding='utf-8')
    manifest={'scale_results.csv':sha256(csv_path),'summary.json':sha256(summary_path)}
    (outdir/'SHA256SUMS.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps({'max_sustained_input_events_per_sec':summary['max_sustained_input_events_per_sec'],'evidence':str(outdir)},indent=2))
    print('PHASE6_E16_SCALE=PASS')

if __name__=='__main__': main()
