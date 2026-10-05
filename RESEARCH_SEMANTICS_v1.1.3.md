# STREAM-SURE v1.1.3 — Research Semantics Freeze

This release freezes the manuscript-aligned decision semantics before publication-grade experiments.

## Canonical outcome ordering

1. A later evidence correction that invalidates a prior certificate enters the `CORRECT` repair workflow.
2. Any mandatory required predicate at `FAIL` yields `REJECT`.
3. Any mandatory required predicate at `UNKNOWN` yields `WAIT`.
4. All mandatory required predicates at `PASS` yields `CERTIFIED`.
5. `PROVISIONAL` is permitted only when the caller explicitly enables a lower-consequence fallback policy and the lower class itself satisfies all of its required predicates.

A high-consequence request therefore cannot silently degrade to a lower assurance class merely because some evidence is unresolved.

## Flagship E15

The same Flink-derived inventory state is evaluated for two decisions while one required warehouse source is absent:

- D0 dashboard observation → `CERTIFIED` because freshness/completeness is not mandatory for D0 in the default policy.
- D3 shipment decision → `WAIT` because freshness/completeness evidence is required and unresolved.

This implements the manuscript proposition that decision readiness is relative to the consequence of the requested action.

## Explicit fallback

Applications that intentionally support degraded operation may set:

- `allow_provisional_fallback=true`
- optional `max_provisional_class`

Only then may the engine issue `PROVISIONAL`, and only if the lower class passes all mandatory predicates.
