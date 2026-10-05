from streamsure.models import *
from streamsure.engine import CertificationEngine
import time, json, argparse, tracemalloc

ap=argparse.ArgumentParser(); ap.add_argument('--n',type=int,default=100000); args=ap.parse_args()
engine=CertificationEngine(); now=time.time()
e=Evidence(); st=DecisionBearingState('scale',1,'inventory',{'committed_inventory':1,'verified_available_inventory':2},e,now-1,now,['a'],{'a':0.1},{'a':True},{'x':'1'},{'a':'1'},'1','lineage://scale',{})
req=DecisionRequest('scale-d',DecisionClass.D2,'scale probe')
tracemalloc.start(); t0=time.perf_counter()
for i in range(args.n):
    st.state_version=i+1
    engine.certify(st,req)
elapsed=time.perf_counter()-t0
cur,peak=tracemalloc.get_traced_memory(); tracemalloc.stop()
print(json.dumps({'operations':args.n,'elapsed_seconds':elapsed,'ops_per_second':args.n/elapsed,'peak_tracemalloc_bytes':peak,'note':'in-process core-engine microbenchmark; not Kafka/Flink throughput'},indent=2))
