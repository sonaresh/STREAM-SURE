# STREAM-SURE Phase 4 - Kafka + Apache Flink distributed acceptance

This phase validates the Kafka/Flink research path:

Kafka `streamsure.events` -> Apache Flink stateful inventory derivation -> Kafka `streamsure.certify.requests` -> STREAM-SURE certification API -> Kafka `streamsure.certificates`.

The smoke test implements the flagship E15 pattern. Warehouse C is intentionally absent. The same Flink-derived state is evaluated for D0 and D3.

## Frozen research-semantics acceptance

Expected outcomes:

- **D0 = CERTIFIED**
- **D3 = WAIT**
- reason for D3: required freshness evidence remains unresolved (`FRESHNESS_UNKNOWN`)

A required `UNKNOWN` produces `WAIT` by default. `PROVISIONAL` requires an explicitly configured lower-consequence fallback policy and must not silently hide required unresolved evidence.

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

The phase passes only when the acceptance markers are printed, the Flink job is RUNNING, and the E15 semantic result is D0 `CERTIFIED` versus D3 `WAIT`.

This is a distributed smoke/acceptance test, not the final E16 publication-scale experiment.
