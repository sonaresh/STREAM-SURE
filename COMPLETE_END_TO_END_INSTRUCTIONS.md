# STREAM-SURE v1.0.1 — Complete End-to-End Instructions

This guide is written for the research lab workflow: Windows 11, VS Code PowerShell, Python, Docker Desktop/WSL2, kubectl, AWS CLI, Terraform, and a short-lived AWS sandbox only when needed.

## Phase 0 — Copy and validate tools

```powershell
cd C:\Users\nares\OneDrive\Desktop\Prototype
Expand-Archive .\STREAM-SURE_End_to_End_Prototype_v1.0.1.zip -DestinationPath .\STREAM-SURE
cd .\STREAM-SURE

python --version
docker version
docker compose version
kubectl version --client
terraform version
aws --version
```

For optional AWS validation later:

```powershell
aws sso login --profile infra-lab
aws sts get-caller-identity --profile infra-lab
aws configure get region --profile infra-lab
```

Do not create AWS resources in Phase 0.

## Phase 1 — Python local acceptance

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .

.\scripts\validate.ps1
```

Pass condition:
- every Python test passes
- `streamsure doctor` reports status `ok`
- `results\smoke\episodes.csv` exists
- `results\smoke\summary.json` exists
- `results\smoke\SHA256SUMS.json` exists

## Phase 2 — Flagship E15 demo

```powershell
.\scripts\run-demo.ps1
```

Expected behavior:
- the same inventory state is evaluated twice
- D0 dashboard observation is `CERTIFIED`
- D3 shipment commitment is `PROVISIONAL` while source freshness/completeness is unresolved
- the higher-consequence request is therefore not authorized as decision-ready

This demonstrates `Ready(S,D_low) != Ready(S,D_high)` without changing the underlying state.

## Phase 3 — API end to end

Terminal 1:

```powershell
.\scripts\run-api.ps1
```

Terminal 2:

```powershell
Invoke-RestMethod http://127.0.0.1:8080/health
Invoke-WebRequest http://127.0.0.1:8080/metrics
```

Use the certification request in `README.md`, then fetch the returned certificate:

```powershell
Invoke-RestMethod http://127.0.0.1:8080/certificates/<certificate_id>
```

## Phase 4 — Repair lineage test

1. Issue a certificate.
2. Register a consuming decision in SQLite through the Python service API or test harness.
3. Submit corrected state using `/repair`.
4. Verify returned outcome `CORRECT` and `affected_decisions`.

The automated test suite already validates this path.

## Phase 5 — Local benchmark

```powershell
.\scripts\run-benchmark.ps1 -Repetitions 20
```

This executes all 16 scenario families over B0-B5.

Important: this is a deterministic research harness. Its numbers validate framework logic and evidence generation, not final Kafka/Flink performance.

## Phase 6 — Core scale microbenchmark

```powershell
.\scripts\run-scale-probe.ps1 -N 100000
```

This measures only in-process certification-engine operations. Do not report it as event-stream throughput.

## Phase 7 — Docker acceptance

```powershell
docker compose build
docker compose up -d
docker compose ps
Invoke-RestMethod http://127.0.0.1:8080/health
```

Persistence check:

```powershell
docker compose restart
Invoke-RestMethod http://127.0.0.1:8080/health
```

Stop:

```powershell
docker compose down
```

## Phase 8 — kind/Kubernetes acceptance

```powershell
docker build -t streamsure:1.0.1 -f docker\Dockerfile .
kind create cluster --name streamsure
kind load docker-image streamsure:1.0.1 --name streamsure
kubectl apply -f kubernetes\deployment.yaml
kubectl -n stream-sure rollout status deployment/streamsure --timeout=120s
kubectl -n stream-sure get all
kubectl -n stream-sure port-forward svc/streamsure 8080:8080
```

In another terminal:

```powershell
Invoke-RestMethod http://127.0.0.1:8080/health
```

Teardown:

```powershell
kind delete cluster --name streamsure
```

## Phase 9 — Kafka/Flink integration milestone

The v1 core package contains a Kafka adapter, but the final paper's distributed experiment still requires actual Kafka/Flink execution. Do not convert the local harness results into journal claims.

Recommended sequence:
1. start local Kafka
2. publish synthetic finance/inventory/security events
3. build the derived state in Flink
4. map event-time/watermark/contract/lineage evidence into DBSS
5. call STREAM-SURE certification
6. persist SSAC
7. inject E1-E15 faults
8. capture Kafka/Flink checkpoint/recovery evidence
9. then perform the E16 throughput sweep

## Phase 10 — Optional AWS validation

Only after local Docker and Kubernetes validation are clean.

Use the configured `infra-lab` SSO profile and the lab's `us-east-2` region. Keep resources short-lived. The core prototype does not require MSK, NAT Gateway, RDS, OpenSearch, Neptune, GPU, or permanent EC2.

Recommended low-cost validation:
- push one image to ECR
- reuse or create a short-lived EKS environment only if necessary for the paper
- store final evidence in a dedicated S3 prefix
- capture manifests, logs, hashes, and timestamps
- destroy experimental resources immediately after evidence capture

## Freeze procedure before manuscript numbers are inserted

```powershell
git init
git add .
git commit -m "Freeze STREAM-SURE v1.0.1 local reference implementation"
git tag streamsure-v1.0.1
```

Then record:
- Git commit SHA
- tag
- Python version
- Docker version
- kubectl version
- Kafka version
- Flink version
- hardware CPU/RAM
- event size
- partitions
- Flink parallelism
- checkpoint interval
- state cardinality
- run duration

Only those frozen runs should populate the manuscript's empirical Results section.


# Phase 6 — E16 Distributed Scale

```powershell
.\scripts\phase6-deploy.ps1
.\scripts\phase6-run.ps1
```

Default sweep is laptop-safe. Only attempt higher enterprise targets after the default sweep is sustained. See `PHASE6_E16_SCALE.md`.
