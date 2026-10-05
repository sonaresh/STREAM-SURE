$ErrorActionPreference='Stop'
function Check { param([string]$What) if ($LASTEXITCODE -ne 0) { throw "$What failed" } }
$Compose='docker-compose.phase6.yml'
Write-Host '==> STREAM-SURE Phase 6 E16 distributed scale environment'
docker compose -f $Compose build; Check 'compose build'
docker compose -f $Compose up -d kafka streamsure jobmanager taskmanager; Check 'core services start'
docker compose -f $Compose run --rm kafka-init; Check 'Kafka topic initialization'
Write-Host '==> Starting eight optimized certification bridge workers'
docker compose -f $Compose up -d --scale bridge=8 bridge; Check 'bridge workers start'
docker compose -f $Compose build flink-job-build; Check 'Flink job build'
docker compose -f $Compose run --rm flink-submit; Check 'Flink submit'
$deadline=(Get-Date).AddSeconds(120); $running=$false; $jobId=$null
while((Get-Date)-lt $deadline){
  try {$o=Invoke-RestMethod http://127.0.0.1:18082/jobs/overview -TimeoutSec 5; if($o.jobs.Count -gt 0){$j=$o.jobs|Sort-Object 'start-time' -Descending|Select-Object -First 1; $jobId=$j.jid; Write-Host ("Flink job {0}: {1}" -f $j.jid,$j.state); if($j.state -eq 'RUNNING'){$running=$true;break}; if($j.state -in @('FAILED','CANCELED','FINISHED')){throw "Flink terminal state $($j.state)"}}} catch{}
  Start-Sleep -Seconds 3
}
if(-not $running){docker compose -f $Compose logs --tail 200 jobmanager taskmanager; throw 'Flink job did not reach RUNNING'}
Write-Host '==> Services'; docker compose -f $Compose ps
Write-Host '==> STREAM-SURE'; Invoke-RestMethod http://127.0.0.1:18081/health | Format-Table
Write-Host 'PHASE6_INFRASTRUCTURE=PASS'
