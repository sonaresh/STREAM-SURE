from __future__ import annotations
from dataclasses import dataclass
from typing import Callable
import time, uuid
from .models import *

@dataclass
class Scenario:
    scenario_id: str
    name: str
    injected_condition: str
    expected_valid: bool
    build: Callable[[], tuple[DecisionBearingState, DecisionRequest]]

def _base(domain="inventory", dc=DecisionClass.D2):
    now=time.time()
    e=Evidence(details={"provisional_max_class":0})
    v={"committed_inventory":50,"verified_available_inventory":100}
    st=DecisionBearingState(
        state_id=f"state-{uuid.uuid4().hex[:8]}", state_version=1, domain=domain, value=v,
        evidence=e,event_time_start=now-1,event_time_end=now,
        required_sources=["source-a","source-b"],source_freshness={"source-a":0.1,"source-b":0.1},
        source_completeness={"source-a":True,"source-b":True},contract_versions={"inventory":"1.0"},
        producer_versions={"source-a":"1.0","source-b":"1.0"},transformation_version="1.0",
        lineage_reference="lineage://demo",uncertainty_context={"score":0.05}
    )
    req=DecisionRequest(decision_id=f"decision-{uuid.uuid4().hex[:8]}",decision_class=dc,purpose="benchmark")
    return st,req

def catalog() -> list[Scenario]:
    def s1(): return _base()
    def s2(): st,r=_base(); st.evidence.details["duplicate_seen"]=True; return st,r
    def s3(): st,r=_base(); st.evidence.temporal=TriState.UNKNOWN; return st,r
    def s4(): st,r=_base(); st.evidence.temporal=TriState.UNKNOWN; st.evidence.details["out_of_order"]=True; return st,r
    def s5(): st,r=_base(); st.evidence.freshness=TriState.UNKNOWN; st.source_completeness["source-b"]=False; return st,r
    def s6(): st,r=_base(); st.evidence.freshness=TriState.FAIL; st.source_freshness["source-b"]=999; return st,r
    def s7(): st,r=_base(); st.contract_versions["inventory"]="1.1-compatible"; return st,r
    def s8(): st,r=_base(); st.evidence.contract=TriState.FAIL; st.evidence.details["semantic_drift"]="gross_to_net"; return st,r
    def s9(): st,r=_base(); st.evidence.contract=TriState.FAIL; st.evidence.details["unit_mutation"]="dollars_to_cents"; return st,r
    def s10(): st,r=_base(); st.value["verified_available_inventory"]=40; return st,r
    def s11(): st,r=_base(); st.evidence.details["recovered_from_checkpoint"]=True; return st,r
    def s12(): st,r=_base(); st.evidence.details["replayed"]=True; return st,r
    def s13(): st,r=_base(); st.evidence.temporal=TriState.UNKNOWN; st.evidence.details["cross_region_delay_ms"]=1500; return st,r
    def s14(): st,r=_base(); st.evidence.details["correction_pending"]=True; st.evidence.temporal=TriState.UNKNOWN; return st,r
    def s15(): st,r=_base(dc=DecisionClass.D3); st.evidence.freshness=TriState.UNKNOWN; st.source_completeness["source-b"]=False; return st,r
    def s16(): st,r=_base(); st.evidence.details["scale_probe"]=True; return st,r
    defs=[
      ("E1","Clean stream","No fault",True,s1),("E2","Duplicate event","Delivery duplication",True,s2),
      ("E3","Late critical event","Delayed business evidence",False,s3),("E4","Out-of-order lifecycle","Incorrect arrival order",False,s4),
      ("E5","Missing source","Required source stalls",False,s5),("E6","Stale enrichment","Reference data ages",False,s6),
      ("E7","Compatible schema change","No semantic fault",True,s7),("E8","Semantic drift","Schema unchanged, meaning changed",False,s8),
      ("E9","Unit mutation","Dollars to cents",False,s9),("E10","Bad transformation","Logic regression",False,s10),
      ("E11","Stream-engine failure","Checkpoint recovery",True,s11),("E12","State replay","Historical reconstruction",True,s12),
      ("E13","Cross-region delay","Geographic source lag",False,s13),("E14","Correction/retraction","Previously emitted fact revised",False,s14),
      ("E15","Decision relativity","Same state, D0 vs D3/D4",False,s15),("E16","High-scale workload","Maximum sustainable throughput",True,s16)
    ]
    return [Scenario(*x) for x in defs]
