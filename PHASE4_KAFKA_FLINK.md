# STREAM-SURE Phase 4 — Kafka + Apache Flink distributed acceptance

This phase validates the distributed research path:

Kafka `streamsure.events` -> Apache Flink stateful inventory derivation -> Kafka `streamsure.certify.requests` -> STREAM-SURE certification API -> Kafka `streamsure.certificates`.

The smoke test implements the flagship E15 pattern. Warehouse C is intentionally absent. The same Flink-derived state is evaluated for D0 and D3. Expected outcomes are D0=CERTIFIED and D3=PROVISIONAL.

## Windows PowerShell

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\phase4-deploy.ps1
.\scripts\phase4-smoke.ps1
.\scripts\phase4-status.ps1
```

Flink UI: http://127.0.0.1:18082
STREAM-SURE API: http://127.0.0.1:18081

## Acceptance

The phase passes only when `PHASE4_E15_DISTRIBUTED_SMOKE=PASS` and `PHASE4_ACCEPTANCE=PASS` are printed and the Flink job is RUNNING.

This is a distributed smoke/acceptance test, not the final manuscript experiment. E1-E15 repetitions, ablations and E16 scale sweeps remain later phases.
