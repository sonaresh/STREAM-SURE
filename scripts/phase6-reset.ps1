$ErrorActionPreference='Stop'
$Compose='docker-compose.phase6.yml'
Write-Host '==> Resetting Phase 6 environment and removing Kafka/API state'
docker compose -f $Compose down -v --remove-orphans
if($LASTEXITCODE -ne 0){throw 'Phase 6 cleanup failed'}
Write-Host '==> Redeploying a clean Phase 6 environment'
& "$PSScriptRoot\phase6-deploy.ps1"
if($LASTEXITCODE -ne 0){throw 'Phase 6 redeploy failed'}
Write-Host 'PHASE6_CLEAN_BASELINE_READY=PASS'
