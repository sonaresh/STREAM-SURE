$ErrorActionPreference = 'Stop'
python -c "from streamsure.phase5 import verify_phase5; import json; r=verify_phase5('evidence/phase5'); print(json.dumps(r, indent=2)); raise SystemExit(0 if r['status']=='PASS' else 1)"
if ($LASTEXITCODE -ne 0) { throw 'Phase 5 evidence verification failed' }
Write-Host 'PHASE5_EVIDENCE_VERIFIED=PASS'
