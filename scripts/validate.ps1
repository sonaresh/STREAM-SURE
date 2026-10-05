$ErrorActionPreference = "Stop"

function Invoke-Checked {
    param(
        [Parameter(Mandatory=$true)][string]$Description,
        [Parameter(Mandatory=$true)][scriptblock]$Command
    )
    Write-Host "==> $Description" -ForegroundColor Cyan
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Description failed with exit code $LASTEXITCODE"
    }
}

Invoke-Checked "Python version" { python --version }
Invoke-Checked "Automated test suite" { python -m unittest discover -s tests -v }
Invoke-Checked "Environment doctor" { python -m streamsure doctor }
Invoke-Checked "Smoke benchmark" { python -m streamsure benchmark --out results\smoke --repetitions 3 }

Write-Host "STREAM-SURE validation completed successfully." -ForegroundColor Green
