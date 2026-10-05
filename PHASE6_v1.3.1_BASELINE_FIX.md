# STREAM-SURE v1.4.1 — E16 Baseline Isolation Fix

This patch corrects two measurement artifacts discovered after an unsustained 10,000 input-events/s run.

1. **Backlog contamination.** The Kafka topics and bridge consumer group persist within a running Phase 6 environment. After an unsustained run, old certification requests can remain queued. A subsequent run can therefore observe no certificates matching its new `run_id` even while the API is busy processing the prior backlog. `phase6-run.ps1` now refuses to start on a non-clean API state by default, and `phase6-reset.ps1` recreates a clean environment.
2. **Low-rate pacing truncation.** The old 50 ms pacing logic rounded `target_eps/4 * 0.05` down to an integer. At 100 input events/s this produced one decision every 50 ms = 20 decisions/s = 80 input events/s. v1.4.1 uses fractional decision credit so low targets are paced accurately.

These fixes do not change STREAM-SURE certification semantics. They only improve experimental isolation and rate generation accuracy.
