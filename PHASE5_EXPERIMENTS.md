# STREAM-SURE Phase 5 — Frozen E1–E15 Correctness Experiments

Version 1.2.0 freezes the correctness experiment harness before scale testing.

## Frozen design

- Scenarios: E1–E15 only. E16 is reserved for Phase 6.
- Cases: 20 independently parameterized cases per scenario.
- Baselines: B0–B5.
- Total baseline episodes: 15 × 20 × 6 = 1,800.
- E15: 20 additional paired same-state D0/D3 evaluations.
- Master seed: 20261004.
- Ground-truth labels are used only after inference for scoring; baseline evaluators do not receive them.

## Outputs

`evidence/phase5/` contains:

- `episodes.csv` — raw paired episodes.
- `aggregate_metrics.csv` — baseline-level metrics and 95% CIs.
- `per_scenario_metrics.csv` — baseline × scenario metrics.
- `mcnemar_b5_vs_baselines.csv` — exact paired McNemar comparisons.
- `e15_decision_relativity.csv` — flagship D0/D3 paired outcomes.
- `summary.json` — machine-readable experiment summary.
- `environment.json` — runtime provenance.
- `SHA256SUMS.json` — evidence integrity manifest.

## Statistical treatment

- Proportion confidence intervals: Wilson 95% CI.
- Paired correctness comparisons: exact two-sided McNemar test.
- Evaluator median latency CI: seeded bootstrap.
- Evaluator latency is **not** distributed Kafka/Flink latency and must not be reported as such.

## Run

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\phase5-run.ps1
```

Success marker:

```text
PHASE5_EXPERIMENTS=PASS
```
