# Phase 5 build validation

This is a package-construction check, **not manuscript evidence**.

The Phase 5 harness was executed in the artifact build environment with the frozen defaults:

- E1–E15
- 20 parameterized cases per scenario
- B0–B5
- 1,800 paired baseline episodes
- 20 E15 D0/D3 paired evaluations

The generated bundle passed SHA-256 verification, episode-count checks, E15 semantics checks, and E16-exclusion checks. The existing 20-test regression suite also passed.

Run `scripts\\phase5-run.ps1` on the research workstation and use only that workstation-generated evidence for the manuscript.
