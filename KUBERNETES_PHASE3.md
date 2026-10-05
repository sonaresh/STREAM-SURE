# STREAM-SURE Phase 3 — kind/Kubernetes Acceptance

This release adds a kind-specific manifest because generic PVC-backed Kubernetes manifests depend on a cluster storage class. The local kind manifest instead uses a single-node hostPath strictly for local research validation.

## Run

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\kind-deploy.ps1
```

Expected endpoint: `http://127.0.0.1:18080/health`

## Validate restart/persistence

```powershell
kubectl get pods -n stream-sure
kubectl delete pod -n stream-sure -l app=streamsure
kubectl rollout status deployment/streamsure -n stream-sure --timeout=120s
Invoke-RestMethod http://127.0.0.1:18080/health
```

## Logs

```powershell
kubectl logs -n stream-sure deployment/streamsure --tail=100
```

## Tear down

```powershell
.\scripts\kind-delete.ps1
```
