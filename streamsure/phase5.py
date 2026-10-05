from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import platform
import random
import statistics
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from .baselines import BASELINES, baseline_ready
from .domains import apply_domain_invariant
from .engine import CertificationEngine
from .models import DecisionClass, DecisionRequest, Outcome, TriState
from .scenarios import catalog
from . import __version__

PHASE5_SCENARIOS = tuple(f"E{i}" for i in range(1, 16))
DEFAULT_CASES = 20
DEFAULT_SEED = 20261004


def _scenario_map():
    return {s.scenario_id: s for s in catalog() if s.scenario_id in PHASE5_SCENARIOS}


def _parameterize(state, scenario_id: str, rng: random.Random, case_index: int):
    """Vary non-label information while preserving each scenario's frozen validity class.

    This is deliberately conservative: the perturbations change quantities, lags,
    producer versions and source timing without exposing the expected label to any
    baseline. Scenario-specific fault semantics remain intact.
    """
    committed = rng.randint(10, 90)
    if scenario_id == "E10":
        available = max(0, committed - rng.randint(1, 20))
    else:
        available = committed + rng.randint(10, 100)
    state.value["committed_inventory"] = committed
    state.value["verified_available_inventory"] = available
    state.state_version = case_index + 1
    state.transformation_version = f"1.{rng.randint(0, 9)}.{case_index}"
    for src in list(state.source_freshness):
        state.source_freshness[src] = round(rng.uniform(0.01, 0.75), 4)
        state.producer_versions[src] = f"{rng.randint(1,3)}.{rng.randint(0,9)}"
    state.uncertainty_context["score"] = round(rng.uniform(0.005, 0.12), 4)

    if scenario_id == "E6":
        state.source_freshness["source-b"] = round(rng.uniform(60, 1200), 3)
    if scenario_id == "E13":
        state.evidence.details["cross_region_delay_ms"] = rng.randint(700, 5000)
    if scenario_id == "E3":
        state.evidence.details["late_event_ms"] = rng.randint(250, 5000)
    if scenario_id == "E4":
        state.evidence.details["reorder_distance"] = rng.randint(1, 12)
    if scenario_id in {"E8", "E9"}:
        state.evidence.details["mutation_case"] = case_index
    return state


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if total <= 0:
        return (0.0, 0.0)
    p = successes / total
    denom = 1 + z*z/total
    centre = (p + z*z/(2*total)) / denom
    half = z * math.sqrt((p*(1-p) + z*z/(4*total))/total) / denom
    low=max(0.0, centre-half); high=min(1.0, centre+half)
    if successes == 0: low = 0.0
    if successes == total: high = 1.0
    return (low, high)


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    xs = sorted(values)
    k = (len(xs)-1)*p
    lo = int(math.floor(k)); hi = int(math.ceil(k))
    if lo == hi:
        return xs[lo]
    return xs[lo]*(hi-k) + xs[hi]*(k-lo)


def bootstrap_median_ci(values: list[float], rng: random.Random, resamples: int = 2000) -> tuple[float, float]:
    if not values:
        return (0.0, 0.0)
    n = len(values)
    medians=[]
    for _ in range(resamples):
        sample=[values[rng.randrange(n)] for _ in range(n)]
        medians.append(statistics.median(sample))
    return (_percentile(medians, .025), _percentile(medians, .975))


def exact_mcnemar_p(b: int, c: int) -> float:
    """Two-sided exact McNemar p-value using Binomial(n=b+c, p=.5)."""
    n=b+c
    if n == 0:
        return 1.0
    k=min(b,c)
    tail=sum(math.comb(n, i) for i in range(k+1)) / (2**n)
    return min(1.0, 2*tail)


def _evaluate_b5(state, req):
    cert = CertificationEngine().certify(state, req)
    return cert.outcome == Outcome.CERTIFIED, cert.outcome.value, list(cert.reason_codes)


def _record_for(baseline: str, scenario, case_index: int, seed: int):
    rng=random.Random(seed)
    state, req = scenario.build()
    state = _parameterize(state, scenario.scenario_id, rng, case_index)
    state.evidence = apply_domain_invariant(state.domain, state.value, state.evidence)

    t0=time.perf_counter_ns()
    if baseline == "B5":
        ready, outcome, reasons = _evaluate_b5(state, req)
    else:
        ready = baseline_ready(baseline, state, req)
        outcome = "READY" if ready else "NOT_READY"
        reasons = []
    latency_ms=(time.perf_counter_ns()-t0)/1e6
    return {
        "baseline": baseline,
        "scenario_id": scenario.scenario_id,
        "scenario": scenario.name,
        "case_index": case_index,
        "case_seed": seed,
        "decision_class": int(req.decision_class),
        "expected_valid": bool(scenario.expected_valid),
        "ready": bool(ready),
        "outcome": outcome,
        "reason_codes": "|".join(reasons),
        "latency_ms": latency_ms,
        "invariant_fail": state.evidence.invariant == TriState.FAIL,
        "temporal": state.evidence.temporal.value,
        "contract": state.evidence.contract.value,
        "lineage": state.evidence.lineage.value,
        "freshness": state.evidence.freshness.value,
        "uncertainty": state.evidence.uncertainty.value,
        "invariant": state.evidence.invariant.value,
        "decision_policy": state.evidence.decision_policy.value,
    }


def _aggregate(records: list[dict], baseline: str, rng: random.Random):
    rs=[r for r in records if r["baseline"]==baseline]
    invalid=[r for r in rs if not r["expected_valid"]]
    valid=[r for r in rs if r["expected_valid"]]
    invariant_cases=[r for r in rs if r["invariant_fail"]]

    invalid_ready=sum(bool(r["ready"]) for r in invalid)
    valid_ready=sum(bool(r["ready"]) for r in valid)
    invariant_detected=sum(not bool(r["ready"]) for r in invariant_cases)
    correct=sum(bool(r["ready"]) == bool(r["expected_valid"]) for r in rs)

    fdrr=invalid_ready/len(invalid) if invalid else 0.0
    vda=valid_ready/len(valid) if valid else 0.0
    ivdr=invariant_detected/len(invariant_cases) if invariant_cases else 0.0
    acc=correct/len(rs) if rs else 0.0
    lat=[float(r["latency_ms"]) for r in rs]

    fdrr_ci=wilson_interval(invalid_ready,len(invalid))
    vda_ci=wilson_interval(valid_ready,len(valid))
    ivdr_ci=wilson_interval(invariant_detected,len(invariant_cases)) if invariant_cases else (0.0,0.0)
    acc_ci=wilson_interval(correct,len(rs))
    med_ci=bootstrap_median_ci(lat,rng)

    return {
        "baseline": baseline,
        "n": len(rs),
        "invalid_n": len(invalid),
        "valid_n": len(valid),
        "correct_n": correct,
        "accuracy": acc,
        "accuracy_ci95_low": acc_ci[0],
        "accuracy_ci95_high": acc_ci[1],
        "fdrr": fdrr,
        "fdrr_ci95_low": fdrr_ci[0],
        "fdrr_ci95_high": fdrr_ci[1],
        "vda": vda,
        "vda_ci95_low": vda_ci[0],
        "vda_ci95_high": vda_ci[1],
        "ivdr": ivdr,
        "ivdr_ci95_low": ivdr_ci[0],
        "ivdr_ci95_high": ivdr_ci[1],
        "premature_certification_rate": fdrr,
        "evaluator_latency_median_ms": statistics.median(lat) if lat else 0.0,
        "evaluator_latency_median_ci95_low_ms": med_ci[0],
        "evaluator_latency_median_ci95_high_ms": med_ci[1],
        "evaluator_latency_p95_ms": _percentile(lat,.95),
        "evaluator_latency_p99_ms": _percentile(lat,.99),
    }


def _per_scenario(records: list[dict]):
    rows=[]
    for b in BASELINES:
        for sid in PHASE5_SCENARIOS:
            rs=[r for r in records if r["baseline"]==b and r["scenario_id"]==sid]
            if not rs:
                continue
            ready=sum(bool(r["ready"]) for r in rs)
            correct=sum(bool(r["ready"]) == bool(r["expected_valid"]) for r in rs)
            ci=wilson_interval(correct,len(rs))
            rows.append({
                "baseline":b,"scenario_id":sid,"scenario":rs[0]["scenario"],"n":len(rs),
                "expected_valid":rs[0]["expected_valid"],"ready_n":ready,
                "correct_n":correct,"accuracy":correct/len(rs),
                "accuracy_ci95_low":ci[0],"accuracy_ci95_high":ci[1],
            })
    return rows


def _mcnemar(records: list[dict]):
    index={(r["baseline"],r["scenario_id"],r["case_index"]):r for r in records}
    rows=[]
    for comparator in [b for b in BASELINES if b != "B5"]:
        b5_better=0; comparator_better=0; both_correct=0; both_wrong=0
        for sid in PHASE5_SCENARIOS:
            case_indices=sorted({r["case_index"] for r in records if r["scenario_id"]==sid})
            for case_index in case_indices:
                a=index[("B5",sid,case_index)]
                c=index[(comparator,sid,case_index)]
                a_ok=(bool(a["ready"]) == bool(a["expected_valid"]))
                c_ok=(bool(c["ready"]) == bool(c["expected_valid"]))
                if a_ok and c_ok: both_correct+=1
                elif a_ok and not c_ok: b5_better+=1
                elif not a_ok and c_ok: comparator_better+=1
                else: both_wrong+=1
        rows.append({
            "comparison":f"B5_vs_{comparator}",
            "both_correct":both_correct,
            "b5_correct_only":b5_better,
            "comparator_correct_only":comparator_better,
            "both_wrong":both_wrong,
            "discordant_n":b5_better+comparator_better,
            "mcnemar_exact_p":exact_mcnemar_p(b5_better,comparator_better),
        })
    return rows


def _run_e15_pairs(cases: int, master_seed: int):
    sc=_scenario_map()["E15"]
    rows=[]
    for i in range(cases):
        seed=master_seed + 150000 + i
        rng=random.Random(seed)
        state, _ = sc.build()
        state=_parameterize(state,"E15",rng,i)
        state.evidence=apply_domain_invariant(state.domain,state.value,state.evidence)
        low=DecisionRequest(decision_id=f"e15-d0-{i}",decision_class=DecisionClass.D0,purpose="observation")
        high=DecisionRequest(decision_id=f"e15-d3-{i}",decision_class=DecisionClass.D3,purpose="shipment")
        c0=CertificationEngine().certify(state,low)
        c3=CertificationEngine().certify(state,high)
        rows.append({
            "case_index":i,"case_seed":seed,"same_state_id":state.state_id,
            "d0_outcome":c0.outcome.value,"d3_outcome":c3.outcome.value,
            "d0_reason_codes":"|".join(c0.reason_codes),"d3_reason_codes":"|".join(c3.reason_codes),
            "decision_relative_success":c0.outcome==Outcome.CERTIFIED and c3.outcome==Outcome.WAIT,
        })
    return rows


def _write_csv(path: Path, rows: list[dict]):
    if not rows:
        path.write_text("",encoding="utf-8"); return
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)


def _hash_manifest(out: Path):
    entries={}
    for p in sorted(out.rglob("*")):
        if p.is_file() and p.name != "SHA256SUMS.json":
            entries[str(p.relative_to(out)).replace(os.sep,"/")]=hashlib.sha256(p.read_bytes()).hexdigest()
    (out/"SHA256SUMS.json").write_text(json.dumps(entries,indent=2,sort_keys=True),encoding="utf-8")
    return entries


def run_phase5(out_dir: str = "evidence/phase5", cases: int = DEFAULT_CASES, master_seed: int = DEFAULT_SEED):
    if cases < 20:
        raise ValueError("Publication-grade Phase 5 requires at least 20 independently parameterized cases per scenario")
    out=Path(out_dir)
    out.mkdir(parents=True,exist_ok=True)
    scenarios=_scenario_map()
    if set(scenarios) != set(PHASE5_SCENARIOS):
        raise RuntimeError("Frozen Phase 5 scenario set E1-E15 is incomplete")

    records=[]
    for sid_num,sid in enumerate(PHASE5_SCENARIOS, start=1):
        sc=scenarios[sid]
        for case_index in range(cases):
            case_seed=master_seed + sid_num*10000 + case_index
            for baseline in BASELINES:
                records.append(_record_for(baseline,sc,case_index,case_seed))

    stats_rng=random.Random(master_seed+999999)
    aggregate=[_aggregate(records,b,stats_rng) for b in BASELINES]
    per_scenario=_per_scenario(records)
    comparisons=_mcnemar(records)
    e15=_run_e15_pairs(cases,master_seed)

    _write_csv(out/"episodes.csv",records)
    _write_csv(out/"aggregate_metrics.csv",aggregate)
    _write_csv(out/"per_scenario_metrics.csv",per_scenario)
    _write_csv(out/"mcnemar_b5_vs_baselines.csv",comparisons)
    _write_csv(out/"e15_decision_relativity.csv",e15)

    e15_success=sum(bool(r["decision_relative_success"]) for r in e15)
    e15_ci=wilson_interval(e15_success,len(e15))
    summary={
        "phase":"Phase 5 - Frozen E1-E15 correctness experiments",
        "stream_sure_version":__version__,
        "master_seed":master_seed,
        "cases_per_scenario":cases,
        "scenarios":list(PHASE5_SCENARIOS),
        "baselines":list(BASELINES),
        "episode_count":len(records),
        "e15_pair_count":len(e15),
        "e15_success_count":e15_success,
        "e15_success_rate":e15_success/len(e15),
        "e15_success_ci95_low":e15_ci[0],
        "e15_success_ci95_high":e15_ci[1],
        "aggregate":{r["baseline"]:r for r in aggregate},
        "notes":[
            "E16 is intentionally excluded from Phase 5 and reserved for Phase 6 scale evaluation.",
            "Evaluator latency is an in-process decision-evaluator micro-latency, not Kafka/Flink end-to-end latency.",
            "Baselines do not receive expected-valid labels or fault annotations during inference.",
            "All confidence intervals for proportions are Wilson 95% intervals; median latency intervals use seeded bootstrap resampling.",
            "Paired B5 comparisons use exact two-sided McNemar tests.",
        ],
    }
    (out/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True),encoding="utf-8")
    env={
        "stream_sure_version":__version__,"python":sys.version,"platform":platform.platform(),
        "machine":platform.machine(),"processor":platform.processor(),"timestamp_utc":time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        "master_seed":master_seed,"cases_per_scenario":cases,
    }
    (out/"environment.json").write_text(json.dumps(env,indent=2,sort_keys=True),encoding="utf-8")

    manifest=_hash_manifest(out)
    return summary, manifest


def verify_phase5(out_dir: str = "evidence/phase5") -> dict:
    out=Path(out_dir)
    manifest=json.loads((out/"SHA256SUMS.json").read_text(encoding="utf-8"))
    mismatches=[]
    for rel,expected in manifest.items():
        p=out/rel
        actual=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
        if actual != expected:
            mismatches.append({"file":rel,"expected":expected,"actual":actual})
    summary=json.loads((out/"summary.json").read_text(encoding="utf-8"))
    episodes=sum(1 for _ in (out/"episodes.csv").open(encoding="utf-8"))-1
    e15=sum(1 for _ in (out/"e15_decision_relativity.csv").open(encoding="utf-8"))-1
    expected_episodes=len(PHASE5_SCENARIOS)*int(summary["cases_per_scenario"])*len(BASELINES)
    checks={
        "hashes_ok":not mismatches,
        "episode_count_ok":episodes==expected_episodes==int(summary["episode_count"]),
        "e15_count_ok":e15==int(summary["cases_per_scenario"]),
        "e15_semantics_ok":float(summary["e15_success_rate"])==1.0,
        "e16_excluded": all(
            line.split(',',2)[1] != 'E16'
            for i,line in enumerate((out/'episodes.csv').read_text(encoding='utf-8').splitlines()) if i > 0 and line
        ),
    }
    return {"status":"PASS" if all(checks.values()) else "FAIL","checks":checks,"mismatches":mismatches}
