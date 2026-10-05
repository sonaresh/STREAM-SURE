$ErrorActionPreference = "Stop"
$cluster = "streamsure-lab"
$image = "streamsure:1.0.3"

function Assert-Exit([string]$message) {
  if ($LASTEXITCODE -ne 0) { throw $message }
}

function Show-Diagnostics {
  Write-Host "==> Kubernetes diagnostics" -ForegroundColor Yellow
  kubectl get pods,pvc,svc -n stream-sure -o wide
  kubectl describe deployment/streamsure -n stream-sure
  $pods = kubectl get pods -n stream-sure -l app=streamsure -o name
  foreach ($pod in $pods) {
    Write-Host "==> Describe $pod" -ForegroundColor Yellow
    kubectl describe $pod -n stream-sure
    Write-Host "==> Logs $pod" -ForegroundColor Yellow
    kubectl logs $pod -n stream-sure --all-containers=true --tail=200
  }
  Write-Host "==> Recent events" -ForegroundColor Yellow
  kubectl get events -n stream-sure --sort-by=.lastTimestamp | Select-Object -Last 40
}

Write-Host "==> Tool versions"
docker version --format '{{.Client.Version}} / {{.Server.Version}}'; Assert-Exit "docker unavailable"
kubectl version --client; Assert-Exit "kubectl unavailable"
kind version; Assert-Exit "kind unavailable"

Write-Host "==> Building secure non-root image $image"
docker build -f docker/Dockerfile -t $image .
Assert-Exit "docker build failed"

$existing = kind get clusters
if ($existing -notcontains $cluster) {
  Write-Host "==> Creating kind cluster $cluster"
  kind create cluster --name $cluster --config kubernetes/kind-config.yaml
  Assert-Exit "kind create failed"
}

Write-Host "==> Using kind context"
kubectl config use-context "kind-$cluster" | Out-Null
Assert-Exit "unable to select kind context"

Write-Host "==> Loading image into kind"
kind load docker-image $image --name $cluster
Assert-Exit "kind load failed"

Write-Host "==> Applying STREAM-SURE"
kubectl apply -f kubernetes/kind-deployment.yaml
Assert-Exit "kubectl apply failed"

Write-Host "==> Waiting for PVC"
kubectl wait --for=jsonpath='{.status.phase}'=Bound pvc/streamsure-data -n stream-sure --timeout=120s
if ($LASTEXITCODE -ne 0) {
  Show-Diagnostics
  throw "PVC did not bind"
}

Write-Host "==> Waiting for rollout"
kubectl rollout status deployment/streamsure -n stream-sure --timeout=180s
if ($LASTEXITCODE -ne 0) {
  Show-Diagnostics
  throw "rollout failed"
}

Write-Host "==> Pod status"
kubectl get pods,pvc,svc -n stream-sure -o wide

Write-Host "==> Health check"
$health = Invoke-RestMethod http://127.0.0.1:18080/health
$health | Format-Table
if ($health.status -ne "ok") { throw "health check failed" }

Write-Host "STREAM-SURE kind deployment completed successfully." -ForegroundColor Green
