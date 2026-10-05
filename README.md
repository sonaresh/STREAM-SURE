# STREAM-SURE Prototype v1.1.3

**Phase 4 adds real Apache Kafka + Apache Flink distributed integration.** See `PHASE4_KAFKA_FLINK.md`.


**Business-Invariant Certification for Decision-Grade Real-Time Enterprise Streams**

Authors: Naresh Somara, Chandrasekhar Reddy Manikiam, Saurav Kumar

This package is the local-first research prototype for STREAM-SURE. It implements the paper's core contribution as executable software: decision-bearing streaming state, decision-relative certification, SSAC evidence, five certification outcomes, retroactive certification repair, E1-E16 scenarios, B0-B5 baselines, and research metrics.

## What is fully runnable now

- deterministic certification engine using PASS / FAIL / UNKNOWN predicates
- five outcomes: CERTIFIED / PROVISIONAL / WAIT / CORRECT / REJECT
- Decision-Bearing Streaming State (DBSS)
- finance, inventory, and security invariants
- SHA-256 sealed Streaming State Assurance Certificates (SSAC)
- durable SQLite certificate/evidence store
- affected-decision tracking for repaired certificates
- REST-like JSON API using Python standard library only
- `/health`, `/certify`, `/repair`, `/certificates/{id}`, `/metrics`
- E1-E16 frozen scenario catalog
- B0-B5 progressive baseline harness
- FDRR, VDA, IVDR, premature-certification rate, P50/P95/P99 timing
- CSV/JSON evidence export plus SHA-256 manifest
- Docker image definition
- Kubernetes deployment
- optional Kafka adapter
- Windows PowerShell validation scripts

## Scientific boundary

The local harness is an executable reference implementation. It does **not** claim that the local in-process benchmark is equivalent to the final Kafka/Flink enterprise experiment. Final journal-scale throughput, recovery, and distributed-runtime claims must come from the later frozen Kafka/Flink/Kubernetes experiment.

## Lab fit

The default workflow is designed for Windows 11 + VS Code PowerShell + Python + Docker Desktop. No AWS resources are required for the core prototype.

## Quick start: PowerShell

```powershell
cd C:\Users\nares\OneDrive\Desktop\Prototype
Expand-Archive .\STREAM-SURE_End_to_End_Prototype_v1.0.1.zip -DestinationPath .\STREAM-SURE
cd .\STREAM-SURE

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .

.\scripts\validate.ps1
```

Expected validation includes unit/API tests, environment doctor output, and a B0-B5 smoke benchmark.

## Flagship decision-relative demo

```powershell
.\scripts\run-demo.ps1
```

The demo evaluates the same inventory state for low- and high-consequence uses. When a required warehouse has not reported, the low-consequence observation can be handled differently from a high-consequence shipment commitment.

## Start API

```powershell
.\scripts\run-api.ps1
```

Then in another PowerShell terminal:

```powershell
Invoke-RestMethod http://127.0.0.1:8080/health
Invoke-WebRequest http://127.0.0.1:8080/metrics
```

### Certification request

```powershell
$body = @{
  state = @{
    state_id = "inv-001"
    state_version = 1
    domain = "inventory"
    value = @{
      committed_inventory = 50
      verified_available_inventory = 100
    }
    evidence = @{
      temporal = "PASS"
      contract = "PASS"
      lineage = "PASS"
      freshness = "PASS"
      uncertainty = "PASS"
      invariant = "PASS"
      decision_policy = "PASS"
    }
    required_sources = @("warehouse-a","warehouse-b")
    source_freshness = @{ "warehouse-a" = 0.1; "warehouse-b" = 0.2 }
    source_completeness = @{ "warehouse-a" = $true; "warehouse-b" = $true }
  }
  decision = @{
    decision_id = "ship-001"
    decision_class = 2
    purpose = "commit shipment"
  }
} | ConvertTo-Json -Depth 8

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8080/certify -ContentType "application/json" -Body $body
```

## Benchmark

```powershell
.\scripts\run-benchmark.ps1 -Repetitions 20
```

Outputs:

- `results/benchmark/episodes.csv`
- `results/benchmark/summary.json`
- `results/benchmark/SHA256SUMS.json`

These are **research-harness results**, not final paper results.

## Docker

```powershell
docker compose build
docker compose up -d
docker compose ps
Invoke-RestMethod http://127.0.0.1:8080/health
```

Stop:

```powershell
docker compose down
```

## Kubernetes / kind

```powershell
docker build -t streamsure:1.0.1 -f docker\Dockerfile .
kind create cluster --name streamsure
kind load docker-image streamsure:1.0.1 --name streamsure
kubectl apply -f kubernetes\deployment.yaml
kubectl -n stream-sure rollout status deployment/streamsure
kubectl -n stream-sure port-forward svc/streamsure 8080:8080
```

Then validate `/health` and `/metrics`.

## Optional Kafka adapter

The core package has zero non-stdlib runtime dependencies. Kafka support is intentionally optional:

```powershell
pip install -r requirements-kafka.txt
$env:KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
```

The adapter does not embed credentials. For MSK or enterprise Kafka, configure authentication externally.

## Research scenario catalog

| ID | Scenario |
|---|---|
| E1 | Clean stream |
| E2 | Duplicate event |
| E3 | Late critical event |
| E4 | Out-of-order lifecycle |
| E5 | Missing source |
| E6 | Stale enrichment |
| E7 | Compatible schema change |
| E8 | Semantic drift |
| E9 | Unit mutation |
| E10 | Bad transformation |
| E11 | Stream-engine failure |
| E12 | State replay |
| E13 | Cross-region delay |
| E14 | Correction/retraction |
| E15 | Decision relativity |
| E16 | High-scale workload |

## Baselines

- B0: At-least-once
- B1: Exactly-once abstraction
- B2: B1 + event-time sufficiency
- B3: B2 + contract assurance
- B4: B3 + lineage/freshness assurance
- B5: STREAM-SURE full decision-relative certification

The local harness models these guarantees as evidence predicates. Final Kafka/Flink experiments must implement the guarantees using the actual runtime.

## Next empirical milestone

1. Run this package locally and freeze commit/tag.
2. Validate Docker.
3. Validate kind/Kubernetes.
4. Integrate Kafka producer/consumer.
5. Add a real Flink operator/job that emits DBSS state.
6. Execute E1-E15 on Kafka/Flink.
7. Run E16 sustainable-throughput sweep on lab hardware.
8. Use a short-lived AWS validation only after local evidence is clean.
9. Replace manuscript placeholders with measured results only.
## v1.1.3 research-semantics freeze

Before publication-grade experiments, v1.1.3 aligns runtime behavior with the manuscript rule: a required `UNKNOWN` produces `WAIT` by default. `PROVISIONAL` now requires an explicit lower-class fallback policy. The distributed E15 acceptance criterion is D0 `CERTIFIED` versus D3 `WAIT` for the same derived state.

## Phase 5 — Frozen correctness experiment campaign (v1.3.0)

After v1.1.3 distributed acceptance is frozen, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\phase5-run.ps1
```

The campaign executes E1–E15 with 20 parameterized cases per scenario across B0–B5 (1,800 paired episodes), creates the dedicated E15 decision-relativity evidence, computes confidence intervals and exact paired McNemar comparisons, and writes a SHA-256 evidence manifest under `evidence/phase5/`. E16 is intentionally reserved for Phase 6.


## Phase 6 E16 scale
See `PHASE6_E16_SCALE.md`. Use `scripts/phase6-deploy.ps1` then `scripts/phase6-run.ps1`.


## v1.4.1 E16 baseline isolation
Before every independent E16 sweep run `scripts/phase6-reset.ps1`. The scale runner now rejects a dirty API state by default and uses fractional rate pacing at low targets. See `PHASE6_v1.4.1_BASELINE_FIX.md`.

## v1.4.1 optimized Phase 6 runtime
The E16 runtime now batches HTTP certification and SQLite persistence and uses persistent bridge connections. Research semantics are unchanged. See `PHASE6_v1.4.1_PERFORMANCE_OPTIMIZATION.md`.

## Phase 6B reproducibility

Run `scripts/phase6b-run.ps1` after a clean `scripts/phase6-reset.ps1`. Evidence is stored in timestamped, non-overwriting directories under `evidence/phase6b/`. See `PHASE6B_REPRODUCIBILITY.md`.

## v1.4.2 Phase 6B evidence integrity patch
The replicated E16 aggregator now treats zero-certificate runs as valid failed observations rather than crashing on missing latency. The campaign runner resets distributed state between target levels and after any unsustained/incomplete repetition so backlog cannot cascade into subsequent evidence. See `PHASE6B_v1.4.2_EVIDENCE_FIX.md`.
