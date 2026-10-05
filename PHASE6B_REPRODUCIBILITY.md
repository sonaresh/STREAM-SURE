# Phase 6B — E16 Reproducibility and Evidence Preservation

Phase 6B freezes STREAM-SURE v1.4.1 runtime semantics and repeats the optimized E16 operating points to quantify run-to-run variation.

## Evidence policy

Every campaign uses a UTC campaign identifier and writes each repetition to a distinct directory. Existing evidence is never intentionally overwritten by the Phase 6B runner.

Default structure:

```
evidence/phase6b/<campaign-id>/
  target_100/run_01/{scale_results.csv,summary.json,SHA256SUMS.json}
  ...
  target_2500/run_30/{...}
  replicate_runs.csv
  aggregate_reproducibility.csv
  reproducibility_summary.json
  SHA256SUMS.json
```

The top-level SHA256 manifest covers the entire campaign. Preserve the directory unchanged after a manuscript-quality run.

## Default replicated experiment

- Targets: 100, 250, 500, 1000, 2500 input events/s
- 30 repetitions per target
- 30 seconds per repetition
- 150 independent distributed runs total
- 4 Kafka input records per certification decision
- Same certification semantics and optimized v1.4.x runtime path

The aggregate report includes median/IQR, bootstrap 95% CI for median P95 latency and certificate throughput, sustained rate, completion ratio, and transport error totals.

## Knee search

After the 30-run campaign, run a smaller boundary study at 3000, 3500, 4000, 4500, and 5000 input events/s. Five repetitions per point are provided as a practical first boundary search. Increase repetitions if the boundary is unstable.

## Scientific rule

Do not infer real-time suitability from completion alone. Report completion, throughput, and latency together. Preserve failed/unsustained runs; they are evidence of the system boundary.

## v1.4.2 robustness rule
Runs with zero completed certificates are retained in completion/sustained statistics and explicitly counted as missing-latency observations. They are not removed. To prevent backlog contamination, reset distributed state between target levels and immediately after any unsustained or incomplete repetition.
