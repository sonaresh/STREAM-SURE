$ErrorActionPreference='Stop'
function Check { param([string]$What) if ($LASTEXITCODE -ne 0) { throw "$What failed" } }

Write-Host '==> Phase 4: Kafka + Flink distributed deployment'
docker compose -f docker-compose.phase4.yml build; Check 'compose build'

docker compose -f docker-compose.phase4.yml up -d kafka streamsure jobmanager taskmanager; Check 'core services start'

Write-Host '==> Creating required Kafka topics'
docker compose -f docker-compose.phase4.yml run --rm kafka-init; Check 'Kafka topic initialization'

Write-Host '==> Starting certification bridge'
docker compose -f docker-compose.phase4.yml up -d bridge; Check 'bridge start'

Write-Host '==> Building Flink job image'
docker compose -f docker-compose.phase4.yml build flink-job-build; Check 'Flink job build'

# Remove any prior jobs from an earlier failed submission in this compose environment.
Write-Host '==> Existing Flink jobs before submission'
docker compose -f docker-compose.phase4.yml exec -T jobmanager /opt/flink/bin/flink list -a

Write-Host '==> Submitting Flink job'
docker compose -f docker-compose.phase4.yml run --rm flink-submit; Check 'Flink submit'

Write-Host '==> Waiting for Flink job to reach RUNNING'
$deadline = (Get-Date).AddSeconds(120)
$running = $false
$lastState = 'UNKNOWN'
while ((Get-Date) -lt $deadline) {
  try {
    $overview = Invoke-RestMethod http://127.0.0.1:18082/jobs/overview -TimeoutSec 5
    if ($overview.jobs.Count -gt 0) {
      $job = $overview.jobs | Sort-Object 'start-time' -Descending | Select-Object -First 1
      $lastState = $job.state
      Write-Host ("Flink job {0}: {1}" -f $job.jid,$job.state)
      if ($job.state -eq 'RUNNING') { $running = $true; break }
      if ($job.state -in @('FAILED','CANCELED','FINISHED')) {
        try {
          $ex = Invoke-RestMethod ("http://127.0.0.1:18082/jobs/{0}/exceptions" -f $job.jid) -TimeoutSec 5
          $ex | ConvertTo-Json -Depth 12 | Write-Host
        } catch {}
        throw "Flink job entered terminal state $($job.state)"
      }
      if ($job.state -eq 'RESTARTING') {
        try {
          $ex = Invoke-RestMethod ("http://127.0.0.1:18082/jobs/{0}/exceptions" -f $job.jid) -TimeoutSec 5
          if ($ex.'root-exception') { Write-Host $ex.'root-exception' }
        } catch {}
      }
    }
  } catch {
    if ($_.Exception.Message -like 'Flink job entered*') { throw }
  }
  Start-Sleep -Seconds 3
}
if (-not $running) {
  docker compose -f docker-compose.phase4.yml logs --tail 200 jobmanager taskmanager
  throw "Flink job did not reach RUNNING within 120 seconds. Last state: $lastState"
}

Write-Host '==> Service status'
docker compose -f docker-compose.phase4.yml ps
Write-Host '==> Flink jobs'
docker compose -f docker-compose.phase4.yml exec -T jobmanager /opt/flink/bin/flink list
Write-Host '==> STREAM-SURE health'
Invoke-RestMethod http://127.0.0.1:18081/health | Format-Table
Write-Host 'PHASE4_INFRASTRUCTURE=PASS'
