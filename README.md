# Polydiagram — Business Flows as Governed Architecture Artifacts

*Open specification, v0.1 draft.*

[![validate](https://github.com/azimuth-ink/polydiagram/actions/workflows/validate.yml/badge.svg?branch=main)](https://github.com/azimuth-ink/polydiagram/actions/workflows/validate.yml)
[![code: Apache-2.0](https://img.shields.io/badge/code-Apache--2.0-blue.svg)](https://github.com/azimuth-ink/polydiagram/blob/main/LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21524083.svg)](https://doi.org/10.5281/zenodo.21524083)

Polydiagram makes **declared business flows** first-class artifacts in an
architecture-as-code system and **binds them to runtime telemetry by
construction**. A flow is a named, versioned, owner-attributed path through a
typed component graph, carrying SLOs and criticality. Its identity
(`flow.id`, `flow.step`) propagates as trace context, so:

- **Coverage is checkable** — a declared step with no attributable telemetry
  is a named observability gap, found in CI/continuous evaluation, not mid-incident.
- **Drift is checkable both ways** — observed-but-undeclared paths and
  declared-but-silent flows are conformance findings (reflexion-model triad).
- **Layers are governed files, not display state** — a base Topology owns
  node/edge identity and layout; network, authn, and authz overlays annotate
  those same identities from separately owned files (include semantics with
  shallow-merge fragments). Click a layer to isolate: identical layout,
  facet-specific annotations — mTLS/X.509 and ports on the network view,
  IAP vs service-account identity on the authn view. Views are versioned
  render presets. The paper names this artifact the *polymorphic diagram*:
  many presentations, one invariant base.
- **The diagram becomes the SRE surface** — live SLO burn, latency, cost, and
  nondeterminism level render onto the *reviewed* architecture canvas, because the
  diagram, the flows, and the telemetry share identity.

The full argument is in the paper: [`paper/polymorphic-diagram-preprint.md`](https://github.com/azimuth-ink/polydiagram/blob/main/paper/polymorphic-diagram-preprint.md).

Builds on and extends: *Flow-Based Telemetry Coverage: A Method for Measuring and
Governing Observability by Business-Flow Consequence* — Gray, 2026,
DOI [10.5281/zenodo.21415948](https://doi.org/10.5281/zenodo.21415948).

## Repository layout

```
paper/     preprint (CC BY 4.0)
spec/      flow descriptor + layered diagram language (JSON Schema 2020-12)
examples/  worked flow, layered topology (network/authn/authz), fragments, view
tools/     reference validators (the CI gates)
```

## Quickstart

```bash
pip install jsonschema pyyaml
python3 tools/validate_flows.py examples/retail-quote.flow.yaml \
        --registry examples/registry-stub.yaml
python3 tools/validate_diagram.py --root . \
        examples/views/security-review.view.yaml --flows-dir examples
```

## Status

v0.1: flow descriptor schema, layered diagram language (Topology/Layer/View + domain profiles), two validators, binding conventions, worked layered example.
Deliberately out of scope (contracts defined, tooling invited): canvas
implementation, trace-topology discovery miner, backend-specific coverage
evaluators. See paper §8–§9 for scope and limitations.

## License

Code and schemas: Apache-2.0 (see `LICENSE`). Paper (`paper/`) and
specification prose (`spec/*.md`): CC BY 4.0.

## Citing

See `CITATION.cff`. A Zenodo DOI is minted per tagged release.
