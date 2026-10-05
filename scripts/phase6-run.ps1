param(
  [string]$Targets='1000,5000,10000,25000,50000',
  [int]$DurationSec=10,
  [switch]$ContinueAfterUnsustained,
  [switch]$AllowDirtyEnvironment
)
$ErrorActionPreference='Stop'
$Compose='docker-compose.phase6.yml'
Write-Host '==> STREAM-SURE Phase 6: E16 distributed scale sweep'
if(-not $AllowDirtyEnvironment){
  try {
    $metrics=(Invoke-WebRequest -UseBasicParsing http://127.0.0.1:18081/metrics -TimeoutSec 5).Content
    $m=[regex]::Match($metrics,'streamsure_certify_total\s+(\d+)')
    if($m.Success -and [int64]$m.Groups[1].Value -gt 0){
      throw "Dirty Phase 6 environment: streamsure_certify_total=$($m.Groups[1].Value). Reset before a baseline sweep with .\scripts\phase6-reset.ps1"
    }
  } catch {
    if($_.Exception.Message -like 'Dirty Phase 6 environment*'){ throw }
  }
}
$args=@('compose','-f',$Compose,'--profile','scale','run','--rm','scale','--targets',$Targets,'--duration-sec',$DurationSec,'--out','/evidence/phase6')
if($ContinueAfterUnsustained){$args += '--continue-after-unsustained'}
& docker @args
if($LASTEXITCODE -ne 0){throw 'Phase 6 scale sweep failed'}
Write-Host '==> API metrics'
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:18081/metrics | Select-Object -ExpandProperty Content
Write-Host 'PHASE6_EXPERIMENTS=PASS'
