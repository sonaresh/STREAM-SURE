# STREAM-SURE v1.4.2

**Business-Invariant Certification for Decision-Grade Real-Time Enterprise Streams**

Author: **Naresh Somara**  
Affiliation: Independent Researcher, USA

STREAM-SURE is a research prototype for decision-relative certification of continuously derived streaming state. It does **not** replace stream-processing guarantees such as exactly-once execution, event time, watermarks, contracts, lineage, or data-quality controls. Instead, it binds state, evidence, decision context, predicate outcomes, reason codes, and certificate lifecycle into an auditable certification object.

## Research status

- Prototype version: **v1.4.2**
- Manuscript: submitted to **Data & Knowledge Engineering** (October 2026)
- Public reproducibility artifacts: included in this repository
- Frozen publication-scale E16 campaign: **210 runs**
- Final local validation: **25/25 tests passed**

The submitted manuscript and frozen evidence should be treated as immutable. Any corrected or extended experiment should use a new version and campaign identifier.

## Core research boundary

```text
ProcessingCorrect(S_t) does not imply DecisionReady(S_t, D)

PredicateEvaluable(S_t, E_t) does not imply CertificationClosed(S_t, D)
```

STREAM-SURE defines a decision-relative certification contract rather than a new predicate language. The same state may be acceptable for one decision and withheld for another.

## Main mechanisms

- Decision-Bearing Streaming State (DBSS)
- decision-relative certification
- PASS / FAIL / UNKNOWN evidence semantics
- Streaming State Assurance Certificate (SSAC)
- outcomes: CERTIFIED / PROVISIONAL / WAIT / CORRECT / REJECT
- retroactive certificate repair
- certificate lineage and affected-consumer tracking
- E1-E16 controlled scenario catalog
- B0-B5 progressive capability baselines

## Flagship E15 behavior

For the same derived inventory state with required freshness evidence unresolved:

- **D0 observation -> CERTIFIED**
- **D3 high-impact automation -> WAIT**

A required `UNKNOWN` does not silently become `PASS`. `PROVISIONAL` is used only when an explicit lower-consequence fallback policy permits it.

## Final validation

The final v1.4.2 local validation on Windows 11 / Python 3.12.10 passed **25/25 automated tests** covering API behavior, DBSS/SSAC semantics, required UNKNOWN -> WAIT behavior, explicit provisional fallback, invariants, repair, affected-consumer tracking, scenario behavior, and Phase 6B aggregation edge cases.

## Correctness campaign

Phase 5 executes E1-E15 with:

- 15 scenarios
- 20 parameterized cases per scenario
- 6 progressive baselines (B0-B5)
- **1,800 total episodes**

For the 300 STREAM-SURE evaluations in the frozen campaign:

- FDRR = 0
- VDA = 1
- IVDR = 1
- premature certification rate = 0

These are controlled benchmark results, not estimates of field error rates.

## Final E16 Phase 6B campaign

Frozen campaign:

```text
results/phase6b/20261004T205422Z/
```

Artifacts:

- `aggregate_reproducibility.csv`
- `replicate_runs.csv`
- `reproducibility_summary.json`
- `SHA256SUMS.json`

The final campaign contains **30 repetitions at each of 7 target input rates = 210 total runs**.

| Target input | Sustained runs | Sustained rate | Median P95 latency |
|---:|---:|---:|---:|
| 100/s | 30/30 | 100.0% | 217.9 ms |
| 250/s | 30/30 | 100.0% | 532.6 ms |
| 500/s | 29/30 | 96.7% | 1.37 s |
| 1000/s | 28/30 | 93.3% | 3.96 s |
| 1250/s | 27/30 | 90.0% | 9.22 s |
| 2250/s | 23/30 | 76.7% | 43.59 s |
| 2450/s | 22/30 | 73.3% | 49.31 s |

Interpretation:

- 100-250 events/s: reproducible low-latency region under the manuscript's explicit P95 < 1 s analysis convention
- 500 events/s: boundary point
- 1000 events/s: latency-degraded region
- 1250 events/s: saturation onset
- 2250-2450 events/s: deep saturation / reliability degradation

Incomplete and zero-certificate runs are retained in reliability statistics. Latency statistics exclude runs with no certificate-latency observation rather than fabricating latency values.

### Important configuration provenance

The deployment script intended to start eight certification bridge replicas, but frozen campaign logs show Docker Compose reconciliation removing replicas 2-8 immediately before measured runs. Therefore, the published E16 results must be interpreted as measurements of an **effective single-bridge certification path**, not an eight-worker scaling result.

## Quick validation

PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .

.\scripts\validate.ps1
```

Phase 6 / Phase 6B requires **Docker Desktop to be running**. If Docker is stopped, a Docker API connection failure from `phase6-reset.ps1` is expected and does not invalidate previously generated evidence.

## Phase 4 Kafka/Flink E15 acceptance

```powershell
.\scripts\phase4-deploy.ps1
.\scripts\phase4-smoke.ps1
.\scripts\phase4-status.ps1
```

Expected flagship outcome:

```text
D0 = CERTIFIED
D3 = WAIT
```

## Phase 6B reproduction

Use a clean deployment state:

```powershell
.\scripts\phase6-reset.ps1
.\scripts\phase6b-run.ps1
```

Do not overwrite the frozen publication campaign. New experiments should use a new campaign directory/version.

## Repository boundary

This GitHub repository contains source code and curated reproducibility results. Full raw evidence is retained separately because of its size. The SHA-256 manifest may reference raw files that are not all stored in GitHub.

## Scientific limitations

The current evidence does **not** establish:

- production-enterprise throughput
- multi-host cluster scalability
- superiority of an external certification service over an equivalently expressive in-engine implementation
- causal contribution of each individual predicate in isolation
- protection against arbitrary Byzantine source behavior

These limitations are explicit in the manuscript.

## Citation

See `CITATION.cff`.

## License

Apache-2.0.
