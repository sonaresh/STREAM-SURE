# STREAM-SURE v1.0.3 Kubernetes fix

v1.0.2 could time out during a kind rollout because the Kubernetes pod required
`runAsNonRoot: true` while the Docker image had no explicit non-root USER.

v1.0.3 fixes this by:
- creating uid/gid 10001 in the image and running the application as that identity;
- setting runAsUser/runAsGroup/fsGroup 10001;
- using a PVC in kind rather than hostPath for durable pod-replacement state;
- retaining readOnlyRootFilesystem, dropped Linux capabilities, no privilege escalation, and RuntimeDefault seccomp;
- adding startup probing;
- printing pod/PVC/event/log diagnostics automatically if rollout fails.

If the old v1.0.2 Deployment exists, `kubectl apply` updates it. The old namespace can also be deleted first for a clean acceptance run.
