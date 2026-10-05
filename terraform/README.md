# Optional AWS validation

For the user's research lab, keep AWS validation short-lived and low-cost. The core v1.0.0 prototype requires **no AWS resources**.

Recommended AWS validation sequence:
1. Build/push the `streamsure:1.0.0` image to ECR.
2. Reuse an existing short-lived EKS research cluster only when a Kubernetes validation is required.
3. Store exported evidence in a dedicated S3 prefix.
4. Destroy any resources created specifically for this experiment immediately after evidence capture.

Do not add NAT Gateway, MSK, RDS, OpenSearch, or permanent EC2 solely to run the core prototype.
