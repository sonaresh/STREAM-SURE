# STREAM-SURE v1.1.3 Phase 4 Fix

This patch fixes Docker Compose variable interpolation in the Kafka topic initializer.

## Root cause

Compose interprets `$topic` before `/bin/bash` runs inside the `kafka-init` container. Because no host/Compose variable named `topic` existed, Compose replaced it with an empty string. Kafka then received `--topic ""` and returned `InvalidTopicException`.

## Fix

The Compose file now uses `$$topic`. Docker Compose converts `$$` to a literal `$`, so the container receives `$topic` and Bash expands it inside the loop.

The three topics created are:

- `streamsure.events`
- `streamsure.certify.requests`
- `streamsure.certificates`

The v1.1.3 Jackson/Flink fixes are retained.
