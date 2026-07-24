# Diagram Language v0.1 — Topology, Layers, Views

Normative definition: [`schemas/diagram.schema.json`](schemas/diagram.schema.json)
(JSON Schema 2020-12; envelope) plus the validator rules DG1–DG9 in
[`tools/validate_diagram.py`](../tools/validate_diagram.py). Rationale and the
operational-surface argument: paper §6 (the *polymorphic diagram*).

## Document kinds

| Kind | Owns | Owned by (typical) |
|---|---|---|
| `Topology` | node/edge **identity** and **layout**; nothing else | architects |
| `Layer` | domain **annotations** on those identities, by reference | domain team (network, security, …) |
| `View` | a versioned render preset: base + layer set + display state | whoever runs the review |

A Layer never redefines topology. A View never defines annotations. Layout
lives only in the Topology — every view of the system is the *same picture*.

## Reference rules (the include mechanism)

Three reference forms, one path discipline:

1. **Structural refs** — `Layer.base`, `View.base`, `View.layers[]`: whole-document
   references. Each layer names its base (adding a layer never touches the base
   file — ownership stays clean); each view's layers must share the view's base (DG8).
2. **Fragment imports** — `imports:` maps a local name to `{path, fragment}` in a
   `*.fragment.yaml` file; annotation `data` pulls one in with `$use: <name>`.
   Fragments are **single-level**: a fragment must not itself contain `$use` (DG5).
3. **Identity refs** — `component:` (registry namespace shared with `flow.spec`
   steps), certificate/policy/credential refs: logical names into other governed
   namespaces, never inline material.

**Path discipline (DG1 + schema):** every file reference is a repo-root-relative
POSIX path. No absolute paths, no `..`, no URLs. Remote includes are a
supply-chain decision this spec refuses in v0.1.

**Merge semantics:** effective annotation = `layer.defaults` ⊕ fragment ⊕ local
(`$use` removed), where ⊕ merges objects recursively and **scalars and arrays
replace** (arrays never concatenate — concatenation is where merge languages go
to die). The *merged* result must satisfy the domain profile (DG6).

## Domain profiles

`metadata.domain` selects the annotation vocabulary:

| Domain | Speaks about | Sketch |
|---|---|---|
| `network` | transport `tcp/udp/unix`; protocol `https/http2/grpc/websocket/smtp/smtps/submission/…`; `port`; `tls {mode: none/tls/starttls/mtls, min_version, certificate {x509, ref, issuer, rotation_days, san}}`; node `zone`/`exposure` | edge `e5`: `submission`, `587`, `starttls` — mail egress; `smtps/465` is the implicit-TLS alternative |
| `authn` | `mechanism: iap/oidc/oauth2/service_account/workload_identity/api_key/mtls_cert/…`; `provider: gcp-iam/azure-ad/okta/…`; `principal`; `credential_ref` (secret reference — literals structurally impossible) | entry node: IAP end-user; interior hops: GCP service accounts |
| `authz` | `model: iam_roles/rbac/abac/policy_engine`; `enforcement_point`; `policy_ref`; `roles[]` | quote node: `iam_roles`, `pricing.invoker` |
| `x-<name>` | anything — bring your own schema via `metadata.annotation_schema` (validated per DG6) | data-classification, cost, compliance layers |
| `flow` | **reserved** — the flow lens is *derived* from `flow.spec` documents, never authored as a Layer (DG7) | |

Semantic rules beyond schema: `mtls` requires a certificate (DG3); network
*edge* annotations must declare a protocol (DG4). Multiple layers per domain
are legitimate (`network-current` vs `network-target`); Views select by layer id.

## Renderer contract (the workspace behavior)

1. **Layout invariance.** Node positions come from the base Topology only.
   Toggling layers never moves a node.
2. **Toggle** = union the enabled layers' annotations onto nodes/edges.
   **Isolate** = show one layer's annotations; edges without annotations in the
   isolated layer render dimmed (present, but visibly unclaimed by this facet).
3. **Badges.** `display.edge_badges` / `node_badges` are `<layer-id>:<dotted.path>`
   selectors into annotation data (`net-transport:tls.mode`), so a View pins
   exactly which facts sit on the picture.
4. **Flow layer (derived).** Selecting a flow highlights its step path and
   carries flow annotations (SLO status, coverage, nondeterminism level) per
   the companion flow spec — same mechanism, generated source.
5. Everything a renderer displays is reconstructible from Git + the telemetry
   store; a View is a PR-able object, not a screenshot.

## Governance

Topologies, layers, fragments, and views are Git-authoritative, change by pull
request, and validate in CI (`tools/validate_diagram.py`, wired in the repo
workflow, including the DG9 cross-check that every flow step's component exists
as a topology node). Layer ownership is the point of the file split: the
network team's PR touches `layers/network.layer.yaml` and nothing else, and a
security-relevant change (an edge dropping from `mtls` to `tls`, a rotation
window growing) is a reviewable diff on exactly one file.

## Open questions (tracked)

- Cross-topology references (one layer annotating multiple bases) — excluded
  v0.1; likely arrives as multi-base Views instead.
- Fragment parameterization (fragments with holes) — excluded; `defaults` +
  override covers observed cases so far.
- Edge *direction* semantics per domain (request vs data-flow vs trust
  direction) — currently implicit in `from`/`to`; candidate v0.2 field.
- **Interaction/sequence views** — the language covers structure (topology +
  facets), not time. The companion agent-dec repository documents its
  interactions in ungoverned Mermaid for exactly this reason. A governed
  interaction view (participants bound to topology node ids, messages as
  typed events) is a v0.2+ candidate.
