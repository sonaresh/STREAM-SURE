from __future__ import annotations
import argparse, json, os, platform, sys, tempfile, time
from dataclasses import asdict
from .service import StreamSureService
from .models import *
from .ssac import verify
from .runner import run
from .api import serve


def demo(db):
    svc=StreamSureService(db)
    now=time.time()
    state=DecisionBearingState('inventory-107',1,'inventory',{'committed_inventory':100,'verified_available_inventory':107},
        Evidence(freshness=TriState.UNKNOWN,details={'provisional_max_class':0}),now-2,now,
        ['warehouse-a','warehouse-b','warehouse-c'],{'warehouse-a':0.2,'warehouse-b':0.2,'warehouse-c':99},
        {'warehouse-a':True,'warehouse-b':True,'warehouse-c':False},{'inventory':'1.0'},{'erp':'2026.10'},'1.0','lineage://inventory-107',{'missing_warehouses':1})
    low=DecisionRequest('dashboard',DecisionClass.D0,'display inventory')
    high=DecisionRequest('ship-100',DecisionClass.D3,'commit shipment')
    c1=svc.certify(state,low); c2=svc.certify(state,high)
    print(json.dumps({'low_consequence':asdict(c1)|{'outcome':c1.outcome.value},'high_consequence':asdict(c2)|{'outcome':c2.outcome.value}},indent=2,default=str))

def doctor():
    print(json.dumps({'python':sys.version.split()[0],'platform':platform.platform(),'cwd':os.getcwd(),'status':'ok'},indent=2))

def main():
    ap=argparse.ArgumentParser(prog='streamsure')
    sub=ap.add_subparsers(dest='cmd',required=True)
    sub.add_parser('doctor')
    d=sub.add_parser('demo'); d.add_argument('--db',default='evidence/demo.db')
    b=sub.add_parser('benchmark'); b.add_argument('--out',default='results/benchmark'); b.add_argument('--repetitions',type=int,default=5)
    s=sub.add_parser('serve'); s.add_argument('--host',default='127.0.0.1'); s.add_argument('--port',type=int,default=8080); s.add_argument('--db',default='evidence/api.db')
    args=ap.parse_args()
    if args.cmd=='doctor': doctor()
    elif args.cmd=='demo': demo(args.db)
    elif args.cmd=='benchmark': print(json.dumps(run(args.out,args.repetitions),indent=2))
    elif args.cmd=='serve': serve(args.host,args.port,args.db)

if __name__=='__main__': main()
