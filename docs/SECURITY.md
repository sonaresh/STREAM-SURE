# Security notes
- No cloud credentials are stored in this repository.
- SQLite evidence digests detect modification of an individual SSAC payload; they are not a distributed trust system.
- Bind the API to 127.0.0.1 for local research unless fronted by authentication/network controls.
- Kubernetes manifest drops Linux capabilities, disables privilege escalation and uses a read-only root filesystem.
- Do not expose this research API publicly without authentication, TLS and rate limiting.
