# Validation plan

## Phase A - local correctness
- run `python -m unittest discover -s tests -v`
- run `streamsure demo`
- run B0-B5 smoke benchmark
- verify evidence SHA-256 manifest

## Phase B - Docker
- build Linux image
- healthcheck
- persistent volume restart test

## Phase C - kind/Kubernetes
- restricted container securityContext
- rollout/health test
- restart persistence test

## Phase D - Kafka/Flink
- actual Kafka topics
- event-time and watermark injection
- Flink checkpoint/recovery
- schema/semantic change injection
- E1-E15 repeated scenario execution

## Phase E - scale
- event-rate sweep that the hardware can sustain
- report actual payload, partitions, parallelism, checkpoint interval, state cardinality and duration
- do not report 1M events/sec unless measured

## Phase F - optional AWS
Use the user's short-lived research lab only after local validation is complete. Capture evidence and destroy resources immediately after the run.
