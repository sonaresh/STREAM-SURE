# STREAM-SURE Phase 6 — E16 Distributed Scale Evaluation

This phase measures the **actual Kafka → Flink → STREAM-SURE API/SQLite → Kafka certificate path**. It does not claim synthetic in-process throughput as distributed throughput.

## Measurement unit
Each certification unit uses four Kafka input records: three warehouse updates plus one decision. Results report both **input events/sec** and **completed certificates/sec**.

## Default sweep
1,000; 5,000; 10,000; 25,000; 50,000 input events/sec for 10 seconds each. The harness stops at the first unsustained target by default. A target is marked sustained only when actual producer rate is at least 90% of target, certificate completion is at least 99%, and producer/consumer errors are zero.

## Enterprise extension
Only after lower targets pass, optionally run:

```powershell
.\scripts\phase6-run.ps1 -Targets '10000,50000,100000,250000,500000,1000000' -DurationSec 30
```

Do not report a target as achieved unless the evidence row has `sustained=true`. A 1M target on a laptop is an attempted target, not an expected result.

## Evidence
- `evidence/phase6/scale_results.csv`
- `evidence/phase6/summary.json`
- `evidence/phase6/SHA256SUMS.json`

The result is intended for RQ7 and E16.
