from __future__ import annotations
from .models import *
from .engine import CertificationEngine

BASELINES = ["B0","B1","B2","B3","B4","B5"]

def baseline_ready(name: str, state: DecisionBearingState, req: DecisionRequest) -> bool:
    e=state.evidence
    if name=="B0":
        return True
    if name=="B1":
        return True  # exactly-once execution alone has no business-readiness predicate in this harness
    if name=="B2":
        return e.temporal == TriState.PASS
    if name=="B3":
        return e.temporal == TriState.PASS and e.contract == TriState.PASS
    if name=="B4":
        return all(x==TriState.PASS for x in [e.temporal,e.contract,e.lineage,e.freshness])
    if name=="B5":
        return CertificationEngine().certify(state,req).outcome == Outcome.CERTIFIED
    raise ValueError(name)
