param([int]$N = 100000)
$ErrorActionPreference = "Stop"
python .\scripts\scale_probe.py --n $N
