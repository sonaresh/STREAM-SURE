# STREAM-SURE v1.4.2 Reproduction Guide

This guide describes how to validate the frozen STREAM-SURE v1.4.2 research prototype and how to reproduce new experiments without modifying the publication evidence.

## Scientific boundary

STREAM-SURE separates stream-processing correctness from decision-relative certification:

```text
ProcessingCorrect(S_t) does not imply DecisionReady(S_t, D)
PredicateEvaluable(S_t, E_t) does not imply CertificationClosed(S_t, D)
```

The framework may be implemented inside a stream processor or as a separate service. The contribution is the certification contract and lifecycle, not mandatory physical separation.

## Validated environment

- Windows 11
- Python 3.12.10
- Apache Kafka 4.1.0
- Apache Flink 1.20.2
- Docker Desktop / Docker Compose

## Local validation

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
.\scripts\validate.ps1
```

The final frozen validation passed **25/25 tests**.

## Flagship E15 acceptance

```powershell
.\scripts\phase4-deploy.ps1
.\scripts\phase4-smoke.ps1
.\scripts\phase4-status.ps1
```

Expected decision-relative result:

- D0 observation -> `CERTIFIED`
- D3 high-impact automation -> `WAIT`
- D3 reason -> `FRESHNESS_UNKNOWN`

## Phase 6B

Docker Desktop must be running before Phase 6 / Phase 6B. If Docker is stopped, Docker API connection failure from `phase6-reset.ps1` is expected.

To run a new campaign:

```powershell
.\scripts\phase6-reset.ps1
.\scripts\phase6b-run.ps1
```

Do **not** overwrite the frozen publication campaign.

## Frozen publication campaign

Campaign ID:

```text
20261004T205422Z
```

Curated results:

```text
results/phase6b/20261004T205422Z/aggregate_reproducibility.csv
results/phase6b/20261004T205422Z/replicate_runs.csv
results/phase6b/20261004T205422Z/reproducibility_summary.json
results/phase6b/20261004T205422Z/SHA256SUMS.json
```

The campaign contains 7 target rates x 30 repetitions = **210 runs**.

## Statistical interpretation

Incomplete and zero-certificate runs remain in sustained/completion statistics.

Latency statistics are computed only for runs with certificate-latency observations. No fabricated latency value is assigned to zero-certificate runs.

The P95 < 1 s threshold used in the manuscript is an **analysis convention for the low-latency region**, not a universal real-time requirement.

## Configuration provenance

The deployment intended eight certification bridge replicas, but frozen logs show Docker Compose reconciliation removing replicas 2-8 before measured scale runs. The E16 results therefore characterize an **effective single-bridge certification path**.

Do not describe the frozen results as eight-worker scaling.

## Evidence integrity

The curated result files are public in GitHub. Full raw campaign evidence is retained separately because of its size.

`SHA256SUMS.json` may reference raw evidence files that are not all stored in this repository.

Treat the frozen v1.4.2 campaign as immutable. Any corrected or extended experiment must use a new version and campaign identifier.

## Scope of claims

The current experiment demonstrates controlled correctness behavior, decision relativity, repair semantics, reproducibility, and a local operating envelope.

It does not establish hyperscale production throughput or multi-host cluster performance.
