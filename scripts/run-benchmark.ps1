param([int]$Repetitions = 20)
$ErrorActionPreference = "Stop"
python -m streamsure benchmark --out results\benchmark --repetitions $Repetitions
