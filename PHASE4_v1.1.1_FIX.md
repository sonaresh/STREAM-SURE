# STREAM-SURE Phase 4 v1.1.3 Fix

Fixes two failures observed in v1.1.0:

1. **Jackson linkage conflict**: the user JAR bundled Jackson 2.18.2 while Flink 1.20.2 provides a different Jackson runtime. The job now uses Flink's shaded Jackson classes and no longer packages external Jackson databind.
2. **Kafka topic startup race**: required topics are now explicitly created before the Flink job or bridge starts.
3. **False-positive deployment success**: `phase4-deploy.ps1` now polls Flink REST and requires `RUNNING`; `RESTARTING`, `FAILED`, or timeout cause deployment failure with diagnostics.
