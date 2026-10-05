# STREAM-SURE v1.0.1 Validation Report

Validation environment used by the build system:
- Python 3.13.5
- Linux x86_64 container runtime
- no external network dependency for core runtime

## Executed validation

| Check | Result |
|---|---|
| Python compilation (`compileall`) | PASS |
| Editable package install (`pip --no-build-isolation -e .`) | PASS |
| Automated tests | 19/19 PASS |
| HTTP `/health` | PASS |
| HTTP `/certify` | PASS |
| SSAC SHA-256 seal verification | PASS |
| Tamper detection | PASS |
| SQLite certificate persistence | PASS |
| Consumer tracking | PASS |
| Retroactive repair / affected decisions | PASS |
| Finance invariant | PASS |
| Inventory invariant | PASS |
| Security invariant | PASS |
| Frozen scenario catalog | 16/16 present |
| E15 same-state/different-decision behavior | PASS |
| B5 versus frozen scenario ground truth | 16/16 PASS |
| B0-B5 smoke benchmark | PASS |
| JSON syntax validation | PASS |
| YAML syntax validation | PASS |
| Embedded credential-pattern scan | no matches |

## Flagship E15 acceptance

The same inventory state with unresolved source freshness produced:
- D0 observation: `CERTIFIED`
- D3 high-impact shipment commitment: `PROVISIONAL`

The D3 request is not certified for execution and is explicitly capped at a lower consequence class.

## Smoke benchmark note

A B0-B5 smoke benchmark was generated under `results/smoke/`. These are deterministic harness outputs used to validate the benchmark pipeline. They are **not** final empirical Kafka/Flink results and must not be copied into the journal manuscript as distributed-system performance evidence.

## Core-engine scale probe

100,000 in-process certification operations completed successfully. The output is saved in `results/scale_probe_100k.json`. This is a Python core-engine microbenchmark only; it is **not** Kafka/Flink event throughput.

## Not executed in this validation environment

The following assets are included but require the user's local lab or cloud environment:
- Docker Desktop build/run
- kind/Kubernetes deployment
- actual Kafka integration
- actual Apache Flink job/checkpoint/recovery
- AWS/EKS validation

These are intentionally not marked PASS until executed in the real lab. This prevents the research artifact from overstating evidence.


## v1.3.0 Phase 6
Adds an evidence-producing distributed E16 scale harness. Distributed rates must be measured on the user lab; no unexecuted Kafka/Flink throughput is claimed by this package.


## v1.4.1 Phase 6 baseline measurement fix
- Fractional producer pacing added for accurate low-rate targets.
- Dirty-environment preflight added to prevent stale Kafka/API backlog from contaminating subsequent E16 sweeps.
- `scripts/phase6-reset.ps1` added for reproducible clean-baseline redeployment.
- Certification semantics unchanged.


## v1.4.1 Phase 6 performance optimization
- Core regression suite: **21/21 PASS**.
- Added `/certify-batch` API regression test.
- SQLite batching, HTTP keep-alive, batched Kafka bridge, and eight bridge workers added.
- Research semantics unchanged from v1.1.3.
- Dockerized E16 performance must be validated on the target Windows/Docker lab before reporting performance gains.

## v1.4.2 Phase 6B evidence fix
The aggregator is now null-safe for zero-certificate runs and the runner isolates target levels plus resets after failed/partial repetitions. Additional regression tests cover empty-latency aggregation primitives and zero-certificate evidence loading.
