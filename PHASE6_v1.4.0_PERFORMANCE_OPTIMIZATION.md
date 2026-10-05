# STREAM-SURE v1.4.1 — Phase 6 Performance Optimization

This release preserves the frozen v1.1.3 certification semantics and optimizes only transport/persistence around the E16 path.

## Changes
- `/certify-batch` endpoint for 1–512 independent certification requests.
- One SQLite transaction per batch via `save_certificates()`.
- WAL + `synchronous=NORMAL`, memory temp store, 32 MiB cache, busy timeout.
- Persistent HTTP/1.1 connections from bridge to API.
- Kafka bridge consumes up to 64 requests at once.
- Kafka output is produced as a batch; one flush and one offset commit per batch.
- Phase 6 deploy scales the bridge to eight workers.
- Certification rules, decision classes, invariant evaluation, SSAC sealing, and WAIT/PROVISIONAL semantics are unchanged.

## Scientific comparison
Use exactly the same clean E16 sweep as v1.3.1. Compare completion ratio, P50/P95/P99 end-to-end latency, certificate throughput, and maximum sustainable input rate. Do not compare against contaminated runs.
