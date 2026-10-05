$Compose='docker-compose.phase6.yml'
docker compose -f $Compose ps
Invoke-RestMethod http://127.0.0.1:18082/jobs/overview | ConvertTo-Json -Depth 10
Invoke-RestMethod http://127.0.0.1:18081/health | Format-Table
