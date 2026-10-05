from __future__ import annotations
import csv, json, time, os, hashlib
from pathlib import Path
from dataclasses import asdict
from .scenarios import catalog
from .baselines import BASELINES, baseline_ready
from .domains import apply_domain_invariant
from .metrics import compute


def run(out_dir="results/run", repetitions=5, baselines=None):
    out=Path(out_dir); out.mkdir(parents=True,exist_ok=True)
    baselines=baselines or BASELINES
    records=[]
    for baseline in baselines:
        for sc in catalog():
            for rep in range(repetitions):
                st,req=sc.build()
                st.evidence=apply_domain_invariant(st.domain,st.value,st.evidence)
                t0=time.perf_counter_ns(); ready=baseline_ready(baseline,st,req); dt=(time.perf_counter_ns()-t0)/1e6
                records.append({"baseline":baseline,"scenario_id":sc.scenario_id,"scenario":sc.name,"rep":rep,
                                "expected_valid":sc.expected_valid,"ready":ready,"latency_ms":dt,
                                "invariant_injected":st.evidence.invariant.value=="FAIL"})
    with open(out/'episodes.csv','w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=records[0].keys()); w.writeheader(); w.writerows(records)
    summary={}
    for b in baselines:
        m=compute([r for r in records if r['baseline']==b]); summary[b]=asdict(m)
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True),encoding='utf-8')
    manifest={}
    for fn in ['episodes.csv','summary.json']:
        p=out/fn; manifest[fn]=hashlib.sha256(p.read_bytes()).hexdigest()
    (out/'SHA256SUMS.json').write_text(json.dumps(manifest,indent=2,sort_keys=True),encoding='utf-8')
    return summary
