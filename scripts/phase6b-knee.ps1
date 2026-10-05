param(
  [string]$Targets='3000,3500,4000,4500,5000',
  [int]$Repetitions=5,
  [int]$DurationSec=30,
  [string]$CampaignId=''
)
$ErrorActionPreference='Stop'
if([string]::IsNullOrWhiteSpace($CampaignId)){$CampaignId='knee-'+(Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')}
& "$PSScriptRoot\phase6b-run.ps1" -Targets $Targets -Repetitions $Repetitions -DurationSec $DurationSec -CampaignId $CampaignId
