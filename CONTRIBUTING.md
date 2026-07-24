# Contributing

This is an early open specification. The most valuable contributions right now:

1. **Spec review** — issues against `spec/01-flow-descriptor.md`, especially the
   async/fan-out representation question (paper §9).
2. **Coverage evaluators** — implementations of the coverage constraint for
   specific telemetry backends.
3. **Discovery** — trace-topology → candidate-flow mining experiments.
4. **Layer domains** — schemas for new `x-*` annotation domains (data
   classification, cost, compliance) per `spec/02-diagram-topology-layers.md`.

Rules of the road: schema changes require a version bump per `apiVersion`;
all examples must pass `tools/validate_flows.py` in CI; keep the descriptor
vocabulary small — additions need a documented rejection of the alternative.
