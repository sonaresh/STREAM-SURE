docker compose -f docker-compose.phase4.yml ps
Write-Host '--- Flink jobs ---'
docker compose -f docker-compose.phase4.yml exec -T jobmanager /opt/flink/bin/flink list
Write-Host '--- bridge logs ---'
docker compose -f docker-compose.phase4.yml logs --tail 50 bridge
Write-Host '--- flink logs ---'
docker compose -f docker-compose.phase4.yml logs --tail 50 jobmanager taskmanager
