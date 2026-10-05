$ErrorActionPreference='Stop'
Write-Host '==> Running distributed E15 smoke test through Kafka -> Flink -> STREAM-SURE -> Kafka'
docker compose -f docker-compose.phase4.yml --profile test run --rm smoke
if ($LASTEXITCODE -ne 0) { throw 'Distributed E15 smoke failed' }
Write-Host '==> API metrics'
(Invoke-WebRequest -UseBasicParsing http://127.0.0.1:18081/metrics).Content
Write-Host 'PHASE4_ACCEPTANCE=PASS'
