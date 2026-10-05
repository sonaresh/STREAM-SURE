$ErrorActionPreference = 'Stop'
$env:PYTHONUNBUFFERED='1'
Write-Host '==> STREAM-SURE Phase 5: frozen E1-E15 experiment campaign'
python -c "from streamsure.phase5 import run_phase5; import json; s,m=run_phase5('evidence/phase5',20,20261004); print(json.dumps({'episode_count':s['episode_count'],'e15_success_rate':s['e15_success_rate'],'B5':s['aggregate']['B5']}, indent=2))"
if ($LASTEXITCODE -ne 0) { throw 'Phase 5 experiment campaign failed' }
Write-Host '==> Verifying evidence bundle'
python -c "from streamsure.phase5 import verify_phase5; import json; r=verify_phase5('evidence/phase5'); print(json.dumps(r, indent=2)); raise SystemExit(0 if r['status']=='PASS' else 1)"
if ($LASTEXITCODE -ne 0) { throw 'Phase 5 evidence verification failed' }
Write-Host 'PHASE5_EXPERIMENTS=PASS'
