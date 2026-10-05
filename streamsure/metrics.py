from __future__ import annotations
from dataclasses import dataclass, asdict
from statistics import median

@dataclass
class Metrics:
    fdrr: float
    vda: float
    ivdr: float
    premature_certification_rate: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    n: int


def percentile(xs, p):
    if not xs: return 0.0
    ys=sorted(xs); k=(len(ys)-1)*p; f=int(k); c=min(f+1,len(ys)-1)
    return ys[f] if f==c else ys[f]*(c-k)+ys[c]*(k-f)

def compute(records):
    invalid=[r for r in records if not r["expected_valid"]]
    valid=[r for r in records if r["expected_valid"]]
    fdrr=sum(1 for r in invalid if r["ready"])/len(invalid) if invalid else 0.0
    vda=sum(1 for r in valid if r["ready"])/len(valid) if valid else 0.0
    injected=[r for r in records if r.get("invariant_injected")]
    ivdr=sum(1 for r in injected if not r["ready"])/len(injected) if injected else 0.0
    premature=sum(1 for r in invalid if r["ready"])/len(invalid) if invalid else 0.0
    lat=[r["latency_ms"] for r in records]
    return Metrics(fdrr,vda,ivdr,premature,percentile(lat,.5),percentile(lat,.95),percentile(lat,.99),len(records))
