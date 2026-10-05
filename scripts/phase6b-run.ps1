param(
  [string]$Targets='100,250,500,1000,2500',
  [int]$Repetitions=30,
  [int]$DurationSec=30,
  [string]$CampaignId='',
  [bool]$ResetBetweenTargets=$true,
  [bool]$ResetAfterUnsustained=$true
)
$ErrorActionPreference='Stop'
$Compose='docker-compose.phase6.yml'
if([string]::IsNullOrWhiteSpace($CampaignId)){$CampaignId=(Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')}
$root="evidence/phase6b/$CampaignId"
Write-Host "==> STREAM-SURE Phase 6B reproducibility campaign: $CampaignId"
Write-Host "==> Evidence root: $root"

# Require a clean initial state. Existing evidence folders are not deleted.
$metrics=(Invoke-WebRequest -UseBasicParsing http://127.0.0.1:18081/metrics -TimeoutSec 5).Content
$m=[regex]::Match($metrics,'streamsure_certify_total\s+(\d+)')
if($m.Success -and [int64]$m.Groups[1].Value -gt 0){
  throw "Dirty Phase 6B start: streamsure_certify_total=$($m.Groups[1].Value). Run .\scripts\phase6-reset.ps1 first."
}

$targetList=$Targets.Split(',') | ForEach-Object {[int]$_.Trim()}
$targetIndex=0
foreach($target in $targetList){
  $targetIndex++
  if($ResetBetweenTargets -and $targetIndex -gt 1){
    Write-Host "==> Resetting distributed state before target $target eps to isolate target-level evidence"
    & "$PSScriptRoot\phase6-reset.ps1"
    if($LASTEXITCODE -ne 0){throw "Phase 6B reset before target=$target failed"}
  }

  for($i=1;$i -le $Repetitions;$i++){
    $run=("run_{0:D2}" -f $i)
    $hostOut="$root/target_$target/$run"
    $containerOut="/evidence/phase6b/$CampaignId/target_$target/$run"
    Write-Host "==> Target $target eps | repetition $i/$Repetitions"
    & docker compose -f $Compose --profile scale run --rm scale --targets "$target" --duration-sec $DurationSec --out $containerOut
    if($LASTEXITCODE -ne 0){throw "Phase 6B target=$target repetition=$i failed"}

    $summaryPath=Join-Path $hostOut 'summary.json'
    if(-not (Test-Path $summaryPath)){throw "Missing Phase 6B summary: $summaryPath"}
    $doc=Get-Content $summaryPath -Raw | ConvertFrom-Json
    $r=$doc.runs[0]
    $completion=[double]$r.completion_ratio
    $sustained=[bool]$r.sustained
    Write-Host ("==> Run outcome: sustained={0} completion={1:P2} certificates={2}/{3}" -f $sustained,$completion,$r.certificates_received,$r.decisions_target)

    # A failed/partial repetition can leave Kafka/bridge work queued. Reset immediately
    # before the next repetition so one failure cannot cascade into later evidence.
    if($ResetAfterUnsustained -and (-not $sustained -or $completion -lt 0.99) -and $i -lt $Repetitions){
      Write-Host "==> Unsustained/incomplete run detected; resetting distributed state before next repetition"
      & "$PSScriptRoot\phase6-reset.ps1"
      if($LASTEXITCODE -ne 0){throw "Phase 6B reset after target=$target repetition=$i failed"}
    }
  }
}

Write-Host '==> Aggregating replicated evidence and computing bootstrap confidence intervals'
python -m streamsure.phase6b --root $root --expected-repetitions $Repetitions
if($LASTEXITCODE -ne 0){throw 'Phase 6B evidence aggregation failed'}
Write-Host "PHASE6B_CAMPAIGN_ID=$CampaignId"
Write-Host "PHASE6B_EVIDENCE_ROOT=$root"
Write-Host 'PHASE6B_REPRODUCIBILITY=PASS'
