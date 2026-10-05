# STREAM-SURE v1.4.2 — Phase 6B Evidence/Aggregation Fix

This patch does **not** change certification semantics or the optimized runtime path.

It fixes two reproducibility problems discovered in a real 150-run Phase 6B campaign:

1. A valid failed run with zero certificates has no latency observations. The v1.4.1 aggregator called `statistics.median([])` and crashed. v1.4.2 retains that run as a failed observation, counts it in completion/sustained statistics, records missing latency explicitly, and computes latency summaries only from runs that actually produced certificates.
2. An unsustained repetition can leave queued Kafka/bridge work and contaminate later repetitions. The v1.4.2 runner resets the distributed environment after an unsustained/incomplete repetition and between target levels, while preserving host evidence directories.

A zero-certificate run is never silently discarded. For publication, report sustained rate, completion distribution, zero-certificate/incomplete-run counts, and latency distributions together.
