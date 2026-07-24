# The Polymorphic Diagram: Binding Declared Business Flows to Runtime Telemetry in Governed Architecture-as-Code

**Jeff Gray** — Independent — [ORCID 0009-0005-6796-6576](https://orcid.org/0009-0005-6796-6576) — [azimuth.ink](https://azimuth.ink)

*Preprint, v0.1 — July 2026. Intended for deposit on Zenodo (CC BY 4.0). Companion open specification and reference tooling: FlowBind (see Data & Code Availability).*

---

## Abstract

Enterprise architecture diagrams and production observability describe the same system from opposite directions, and in most organizations the two never meet. Diagrams are declared top-down, encode business intent, and go stale the day they are drawn. Service maps are inferred bottom-up from traffic, are always current, and carry no intent: they cannot say which paths *matter*, what a path is *for*, or what its owner promised about it. This paper describes a pattern — flow-bound architecture — that closes the gap by making **business flows first-class, governed artifacts** inside an architecture-as-code system. A flow is a declared, versioned path through a typed component graph, carrying business ownership, criticality, and service-level objectives. Flow identity is propagated into runtime telemetry as trace context, so every span, metric point, and cost record is attributable to a declared flow. Three properties follow. First, *coverage* becomes checkable: a declared flow step with no corresponding telemetry is a named observability gap, not an unknown unknown. Second, *drift* becomes checkable in both directions: observed paths that match no declared flow, and declared flows with no observed traffic, are conformance findings in the sense of software reflexion models. Third, the architecture canvas itself becomes an operational surface: because nodes and edges on the diagram are the same identities that appear in telemetry, live SLO status, cost, and nondeterminism levels render directly onto the declared diagram, turning the design artifact into an SRE console. We name the resulting artifact a *polymorphic diagram*: one governed base presenting as many diagrams, along orthogonal — independent, composable — facets (network, identity, flow, cost) over an invariant identity-and-layout base. The pattern extends the author's previously published flow-based telemetry coverage method (Zenodo, DOI 10.5281/zenodo.21415948) from an observability-governance discipline into a closed architecture-governance loop. We situate the pattern between architecture description languages, service-mesh topology inference, SLO practice, and process mining; define the flow descriptor and its telemetry binding; describe the governance model (Git-authoritative artifacts, runtime stores as rebuildable projections, infrastructure materialized through policy-scanned composition); and discuss limitations including attribute cardinality, sampling floors, asynchronous fan-out, and partial adoption. An open specification with JSON Schema definitions and a reference validator accompanies the paper.

**Keywords:** software architecture, observability, architecture-as-code, distributed tracing, service level objectives, business process observability, conformance checking, site reliability engineering

---

## 1. Introduction

Two artifacts claim to describe a production system's shape.

The first is the architecture diagram: drawn by architects, reviewed in design forums, encoding intent — this component exists to serve that business capability; this path is how a customer transaction is supposed to move. Diagrams carry exactly the information operations teams most need during an incident (what is this thing *for*, who owns it, what did we promise about it) and are almost never trustworthy at the moment of the incident, because nothing forces them to track reality.

The second is the service map: inferred by the observability platform from traces and network telemetry. It is accurate by construction and nearly mute about meaning. It shows that service A called service B forty thousand times in the last hour; it cannot say whether those calls constitute the *quote-issuance* flow the business bet the quarter on, or background cache warming. Inferred maps have no notion of a path that *should* exist but is silent, because they only contain what happened.

The industry has largely accepted this split: design-time artifacts for humans, runtime maps for machines, and tribal knowledge to bridge them. The consequences are familiar. Observability coverage is assessed anecdotally ("I think we trace that path") because there is no machine-readable statement of which end-to-end paths must be observable. Incident response begins with a topology-reconstruction phase. SLOs, where they exist, attach to services rather than to the business transactions users actually experience, so a "green" dashboard can coexist with a broken customer journey that merely crosses many individually-healthy services. And architecture governance — review boards, approved patterns, security gates — operates on documents that the running system is free to ignore.

This paper argues the split is not necessary, and that the bridge is a small, specific artifact: the **declared business flow**, governed with the same rigor as infrastructure code and bound to telemetry by construction rather than convention.

The contribution is a pattern, an artifact model, and an open specification:

1. **Flows as first-class governed artifacts** (§3). A flow is a named, versioned, owner-attributed path over a typed component graph — the same graph that generates the architecture diagram and materializes the infrastructure. Flows live in Git, change by pull request, and carry SLOs and criticality as reviewable fields.
2. **Telemetry binding** (§4). Flow identity propagates through execution as trace context (`flow.id`, `flow.step`), making the declared artifact and the runtime signal joinable by key rather than by inference. Coverage — "every declared step emits at least the signals the flow requires" — becomes a checkable constraint, evaluated continuously.
3. **Bidirectional conformance** (§5). Declared-but-unobserved and observed-but-undeclared paths are both surfaced, adapting the reflexion-model idea [Murphy et al. 2001] from static code structure to live transaction topology, with process-mining techniques [van der Aalst 2016] supplying the discovery direction.
4. **The diagram as operational surface — the polymorphic diagram** (§6). Because diagram nodes, flow steps, and telemetry attributes share identity, the governed diagram renders live: per-flow SLO burn, latency, cost, and nondeterminism level overlay the declared topology. The artifact architects review is the artifact SREs watch.
5. **A governance and materialization substrate** (§7) in which all of the above are Git-authoritative, runtime databases are rebuildable projections, and diagram nodes correspond to real infrastructure because they are materialized through versioned, policy-scanned composition — so the picture is not merely annotated with reality; it is causally connected to it.

We deliberately present this as an architecture pattern with an open specification and reference tooling rather than as an empirical evaluation: the paper reports design reasoning and the constraint language, not benchmark claims, and §9 states limitations candidly.

## 2. Related Work

**Architecture description and architecture-as-code.** Structured architecture modeling spans formal ADLs through pragmatic notations such as the C4 model [Brown] and its tooling (e.g., Structurizr), where diagrams are generated from a versioned model rather than drawn. The viewpoints-and-views tradition — Kruchten's 4+1 model [1995] and ISO/IEC/IEEE 42010 — long ago established that one architecture warrants many stakeholder views; the polymorphic diagram is that tradition made governable and live: views become versioned artifacts (layers and Views over a shared identity base) joined to runtime signal, rather than separately maintained documents. Flow-bound architecture assumes this discipline as its substrate and extends it in one direction: C4-style models describe *structure* (containers, components, relationships); flows add *behavioral paths with business identity and objectives* as peer artifacts, and — critically — a binding contract to runtime telemetry, which model-only approaches do not attempt.

**Runtime topology inference.** Commercial observability platforms and service meshes derive live dependency maps from traces and mesh telemetry (e.g., mesh topology views such as Kiali for Istio). These are the bottom-up half of our picture. They differ from declared flows in provenance (inferred vs. asserted), in stability of identity (an inferred edge has no owner, version, or objective), and in their inability to represent *absence* — a path that should exist and does not. We treat inferred topology not as a competitor but as the evidence stream against which declarations are checked (§5).

**SLOs and SRE practice.** The SLO discipline [Beyer et al. 2016] gives us the objective vocabulary flows carry. The pattern's delta is *attachment point*: SLOs here attach to declared end-to-end flows rather than to services, aligning the unit of reliability accounting with the unit of business meaning. Service-level SLOs remain useful and composable underneath.

**Software reflexion models and conformance checking.** Murphy, Notkin, and Sullivan's reflexion models [2001] compare a declared high-level model against extracted source structure, classifying relations as convergent, divergent, or absent. We adopt the triad wholesale and change the extraction source: instead of static code dependencies, the extracted model is live trace topology, so conformance is evaluated continuously against production behavior rather than at analysis time against code.

**Process mining and business-process observability.** Process mining [van der Aalst 2016] discovers process models from event logs and checks logs against reference models. Flow-bound architecture is the infrastructure-layer analogue: distributed traces are the event log; declared flows are the reference model; discovery proposes candidate flows for governance rather than replacing declaration. Recent interest in mapping OpenTelemetry data to process-mining event abstractions makes this bridge increasingly practical.

**Flow-based telemetry coverage.** The immediate ancestor of this work is the author's flow-based telemetry coverage method [Gray 2026], which discloses declaring critical cross-service flows as first-class entities, scoring each by business consequence to derive a priority tier, algorithmically decomposing flow-level SLAs into per-segment SLOs, specifying the telemetry each segment requires, computing a multi-dimensional coverage score (not "does instrumentation exist" but "can the available telemetry answer the detect/debug/resolve questions when the flow degrades"), and enforcing coverage in CI so changes that reduce observability of high-consequence flows are blocked — all realized over standard tracing with a declared `flow.*` attribute namespace. The present paper embeds that method in a governed architecture-as-code substrate and contributes what the coverage method deliberately did not: the flow's residence *inside* the versioned component/diagram model, conformance in the reverse direction (observed-but-undeclared drift), materialized correspondence between diagram and infrastructure, and the live diagram as the operational surface.

**Telemetry standards.** OpenTelemetry provides the propagation mechanics (context and baggage) and the convention system into which flow attributes fit naturally as a semantic-convention extension. Nothing in the pattern requires proprietary agents; the binding is attributes on standard signals.

**Supply-chain and provenance systems.** Git-authoritative governance with policy-scanned materialization is congruent with provenance frameworks such as in-toto [Torres-Arias et al. 2019] and SLSA; we rely on that congruence in §7 and, in a companion line of work on deterministic execution certificates, extend evidence capture to the execution layer.

To our knowledge, the specific synthesis — business flows as *governed, versioned, SLO-carrying* artifacts whose identity is *propagated into telemetry by construction*, with the *declared diagram doubling as the live operational surface* — has not been articulated as an integrated, open pattern, though every ingredient is individually established. That is deliberate: the pattern's value is the closed loop, and its plausibility rests on the maturity of its parts.

## 3. The Artifact Model

### 3.1 Substrate: the governed component graph

Flow-bound architecture presumes an architecture-as-code substrate with four properties:

1. **Typed components.** Every deployable or logical unit is a registry entry with an identity (`payments.quote-engine`), a category, and **typed ports** — named inputs and outputs with declared types and a compatibility matrix. Ports make paths well-formed: an edge is legal only if port types agree.
2. **Diagrams as data.** The architecture diagram is generated from a node/edge document (components, edges, layout), not drawn; the document is the artifact, the picture is a view. The document is also *layerable*: separately owned overlay documents annotate its identities from other files (§6).
3. **Git as authority.** Registry entries, diagram documents, and flows are files in version control, changed by pull request, validated in CI against published JSON Schemas. Any runtime database that serves these artifacts (for editor speed, for query) is a **rebuildable projection** — deletable and reconstructible from Git, never written to as a source of truth.
4. **Materialized correspondence.** Diagram nodes correspond to real infrastructure because infrastructure is created *from* the registry through versioned composition (§7). The diagram is not documentation of the deployment; the deployment is a function of the diagram's underlying model.

None of these is exotic; each exists separately in mature organizations. The flow artifact is what makes their combination pay.

### 3.2 The flow descriptor

A **flow** declares one business-meaningful path through the component graph:

```yaml
apiVersion: flow.spec/v0.1
kind: Flow
metadata:
  id: quote-issue
  name: "Retail quote issuance"
  version: 1.3.0
  owner: { business: retail-products, technical: team-quotes }
  criticality: tier-1        # tier-1 | tier-2 | tier-3
spec:
  trigger: { type: user_interaction, description: "Customer submits quote request" }
  steps:
    - { id: s1, component: edge.api-gateway,       op: receive }
    - { id: s2, component: identity.session,        op: authorize }
    - { id: s3, component: payments.quote-engine,   op: price,   kind: sync }
    - { id: s4, component: risk.limits-check,       op: evaluate, kind: sync }
    - { id: s5, component: docs.render,             op: generate, kind: async }
    - { id: s6, component: notify.customer,         op: deliver,  kind: async }
  slos:
    availability: 99.9
    latency_p95_ms: 1800        # trigger → s4 (synchronous frontier)
    async_completion_p99_s: 120 # trigger → s6
  telemetry:
    required_signals: [trace, metric]
    attribute_namespace: flow
    sampling_floor: 0.10        # minimum trace sampling for this flow
```

Design points worth defending:

**Flows reference the graph; they do not restate it.** A step names a component (and, in the full specification, the port-level edge it traverses); the wiring's legality is validated against the registry's port types. The flow adds only what the graph cannot know: sequence-with-meaning, ownership, objectives, and criticality.

**Ownership is dual.** `owner.business` names who cares that the flow works; `owner.technical` names who is paged. The split reflects reality in every large organization and makes the flow the artifact where the two meet — reviewably, in a pull request.

**SLOs live on the flow.** Latency and availability are declared where the user experiences them: end to end, with an explicit synchronous frontier (the last step the user waits for) distinguished from asynchronous completion. Service-level objectives remain as derived or supporting objectives.

**Criticality is a field, not folklore.** Tiering drives sampling floors, alert routing, and review depth mechanically; tiers may be hand-assigned or derived from business-consequence scoring per the coverage method [Gray 2026].

**The vocabulary is deliberately small.** Trigger, steps (with `sync|async|fanout|choice` kinds), SLOs, telemetry requirements. Everything else stays in the registry or in operational tooling. Small vocabularies survive governance; large ones die in committee.

### 3.3 Flows are curated, not exhaustive

A system has an unbounded number of runtime paths and a small number of paths that constitute its business. Flows declare the latter — typically dozens per platform, not thousands. This restraint is what makes the telemetry binding cheap (§4, cardinality) and the governance real (someone can actually review the set). Undeclared paths are not illegal; they are *unclaimed*, and §5 shows how the system surfaces them for triage: declare, exempt, or investigate.

## 4. Telemetry Binding

### 4.1 Propagation

At the flow's trigger, the entry component resolves which flow is beginning — from route, event type, or explicit client hint — and stamps the execution context:

```
flow.id       = quote-issue
flow.version  = 1.3.0
flow.step     = s1            # updated at each declared step boundary
```

The attributes travel as trace context/baggage (OpenTelemetry's mechanics fit exactly) and are recorded on every span; metrics exemplars and cost/usage ledger records carry the same keys. From that point, *joinability replaces inference*: any signal in the platform can be grouped, filtered, or budgeted by declared flow with an index lookup, not a topology reconstruction.

Two implementation notes matter in practice. First, **step stamping is boundary instrumentation**, not per-function tracing: the component hosting step `s3` sets `flow.step=s3` on its server span; interior spans inherit. The instrumentation burden is one attribute-set per declared step, which is why curated flow sets stay cheap. Second, **components are flow-agnostic by default**: a component participates in whatever flows traverse it and needs no per-flow code; only entry points resolve flow identity.

### 4.2 The coverage constraint

The flow's `telemetry` block is a *constraint*, and this is the heart of the pattern's observability payoff:

> For flow F with required signal set S and sampling floor r: over any evaluation window, every declared step of F must be evidenced by signals in S attributable to F, and F's effective trace sampling must be ≥ r.

Coverage evaluation is mechanical: query spans grouped by (`flow.id`, `flow.step`) over the window; compare against the declared step set; report the difference. The binary step-evidence form given here is the *minimal* instance of the constraint; the multi-dimensional scoring of [Gray 2026] — whether the available telemetry can answer each segment's detect, debug, and resolve questions, with CI gating by consequence tier — composes onto the same declared artifacts unchanged. A declared step with no evidence is a **named blind spot** — "step s5 of quote-issue (docs.render) emitted no attributable telemetry this week" — which is a work item with an owner, as opposed to the traditional situation, where the same gap is discovered mid-incident.

The constraint is checkable *before* runtime too, in weaker form: static analysis can verify that each step's component contains boundary instrumentation for the flow attributes (the spec-first stance: define the constraint language first, so analyzers have something normative to check; enforcement tooling follows). The two checks are complementary by construction — static analysis catches never-instrumented steps at review time; runtime evaluation catches broken, sampled-out, or misconfigured instrumentation continuously.

### 4.3 Attribution beyond traces

Because cost records and nondeterminism accounting carry the same keys, per-flow unit economics fall out: cost per `quote-issue` execution, token spend per flow for LLM-backed steps, and — where the platform classifies step determinism (from fully deterministic ND0 through open generation ND3, per the companion certificate work) — a *nondeterminism profile per business flow*. "Which business journeys depend on open-ended generation, and what does each cost?" becomes a query.

## 5. Bidirectional Conformance

With declarations on one side and trace-derived topology on the other, the reflexion triad applies directly, evaluated continuously:

**Convergent.** Observed traffic matches a declared flow's steps in order. Healthy; feeds the live surface (§6).

**Absent (declared, unobserved).** A flow — or step — with zero attributable traffic over its evaluation window. Interpretations differ by context and the finding routes accordingly: dead flow (retire it, by PR, leaving history), broken instrumentation (coverage violation, §4.2), or genuinely dormant path (seasonal; annotate with an expected-traffic calendar). The vital property: *silence is now a signal*, which inferred-only maps structurally cannot provide.

**Divergent (observed, undeclared).** Trace topology shows recurring paths matching no flow. Process-mining-style discovery over the trace log clusters them into candidate flows and opens governance items: declare (a real business path nobody wrote down — common in year one), exempt (infrastructure chatter: health checks, cache warming, replication), or investigate (the interesting residue — sometimes an unauthorized integration, sometimes an incident in progress). Divergence detection turns architecture drift from an annual-audit discovery into a weekly diff.

Conformance findings are artifacts too — written to a runs/findings area with the commit SHAs of the flow set they were evaluated against, so "what did we know and when" has an answer.

## 6. The Diagram as Operational Surface

Everything so far could terminate in reports. The pattern's most visible payoff is that it need not: because the diagram document, the flow steps, and the telemetry attributes share identity, the governed diagram renders *live*.

Concretely, the same node-graph canvas that architects use to author and review (nodes from the registry, edges validated by port types, layout embedded in the document) gains an operational mode:

- **Flow lens.** Selecting a flow highlights its declared path across the topology; steps carry live status chips — p95 latency vs. objective, error rate, SLO burn rate, last-hour cost, nondeterminism level where applicable.
- **Coverage shading.** Steps failing the coverage constraint render distinctly (the blind spot is *visible on the map*), as do components not bound to any flow — undeclared territory shown as such, which makes partial adoption honest rather than misleading.
- **Drift overlay.** Divergent observed edges appear as a distinct edge style on the declared topology: the diagram shows what is happening that nobody claimed.
- **Incident entry.** An alert on `quote-issue` SLO burn deep-links to the canvas with the flow lens active — responders start from a picture that is guaranteed current *for the declared path*, with owner and objective attached, and can pivot to raw traces from any step chip.

The flow lens is one instance of a general **layer mechanism** in the open specification. The base topology document owns node/edge identity and layout; separately owned *layer* documents — network, authentication, authorization, or schema-carrying extension domains — annotate those same identities by reference, composing across files with include semantics (repo-relative refs, shallow-merge fragments) rather than duplication. Toggling or isolating a layer preserves the layout exactly and swaps the annotation set: the security reviewer sees, on the identical picture the architect approved, that an interior hop is mTLS with an X.509 identity on 8443 rotating every 30 days, that mail egress runs submission/587 with STARTTLS, that the entry node authenticates end users through an identity-aware proxy while interior edges ride service-account identities. Flows project onto the same mechanism as a *derived* layer, and named Views — base plus layer set plus display state — are versioned artifacts in their own right, so "the security review view" is a PR-able object, not a screenshot. This is the precise sense in which the title's artifact is *polymorphic*: the presentation varies along orthogonal facets; the identity and layout beneath never do.

Two properties distinguish this from a conventional dashboard. First, **the surface is the reviewed artifact**. There is no translation step in which a dashboard author re-encodes (and mis-encodes) the architecture; the SRE view *is* the architect's document with data joined on. When the architecture changes by pull request, the operational surface changes in the same commit. Second, **intent is co-located with signal**. The console answers "what is this, who owns it, what did we promise" in the same glance as "is it healthy" — precisely the pairing that pages currently lack.

The projection discipline (§3.1) applies here as everywhere: the canvas reads fast projections (a topology cache, pre-aggregated SLI series), but every pixel is reconstructible from Git plus the telemetry store. The dashboard cannot drift from the architecture because it has no independent existence.

## 7. Governance and Materialization

The loop closes only if the diagram's nodes are true. Two mechanisms make them true rather than aspirational.

**Git-authoritative artifacts with CI gates.** Registry entries, diagrams, and flows change by pull request; CI validates against the published JSON Schemas (the open specification ships these), checks referential integrity (every flow step resolves to a registry component and a legal port traversal), and rejects unreviewable content (no secret literals; prompt and template references point to versioned files). Review is thereby *possible*: a flow PR shows exactly the business path, objective, or ownership change under discussion. Runtime stores are projections rebuilt on merge.

**Policy-scanned materialization.** Components declare how they become infrastructure: a composition reference into a registry of versioned infrastructure modules, with semantic-version pins and an upstream-update policy (flag/block/auto-PR). Materialization runs through a contained pipeline — compose, validate, lint, security-scan (e.g., tflint/checkov/tfsec-class tooling), plan, and a manual apply gate — and writes an **audit capsule**: the commit SHAs of descriptor/registry/flows, the plan, scan findings, and post-deploy conformance results. The consequence for this paper's argument is simple but load-bearing: a node on the canvas corresponds to infrastructure whose provenance is recorded, so the live overlay in §6 is joined onto a topology that is *known*, not believed.

Governance flags themselves (mandatory steps, criticality tiers, sampling floors) live authority-side in the artifacts, so changing an operational guarantee is a visible diff — never a console toggle.

## 8. Reference Implementation Sketch

The companion repository provides the minimum viable loop:

1. **Schemas** (JSON Schema 2020-12) for the flow descriptor, versioned per `apiVersion`.
2. **Validator** (`tools/validate_flows.py`): schema validation plus referential checks (step-ID uniqueness, component resolution against a registry stub, SLO sanity) — the CI gate, wired in a provided GitHub Actions workflow.
3. **Binding conventions** (`examples/telemetry-binding.md`): the `flow.*` attribute set expressed as an OpenTelemetry semantic-convention extension, with propagation guidance and a worked coverage query.
4. **A worked example** flow (`examples/retail-quote.flow.yaml`) exercising sync/async kinds and the coverage constraint.
5. **The layered diagram language** (`spec/schemas/diagram.schema.json`, `spec/02-diagram-topology-layers.md`): Topology/Layer/View documents with include semantics, domain profiles (network, authn, authz, `x-*`), and `tools/validate_diagram.py` enforcing reference integrity, fragment merge, domain vocabularies, and the flow↔topology cross-check — with a worked layered example (network/authn/authz over the retail-quote topology, from mTLS interior hops to STARTTLS mail egress).

Deliberately out of scope for v0.1, and stated as such: the canvas implementation (any node-graph UI over the diagram document suffices), the discovery miner, and turnkey coverage evaluation for specific backends. The specification defines the contracts these tools must honor; the pattern is tooling-agnostic by design.

## 9. Limitations and Honest Costs

**Cardinality.** `flow.id`/`flow.step` are low-cardinality by construction (curated flows, enumerated steps) — this is the reason curation is a design commitment, not a convenience. Organizations that let flow sets grow unboundedly will meet metric-label cardinality costs; the spec's answer is governance (flows are reviewed artifacts), not technology.

**Sampling.** Coverage evaluation is sensitive to trace sampling; a sampled-out step is indistinguishable from an uninstrumented one at low volumes. Flows therefore declare sampling floors, and tier-1 flows justify tail-based or flow-targeted sampling. This is an operating cost the pattern makes explicit rather than one it removes.

**Asynchronous and fan-out reality.** Step kinds cover common shapes, but long-gap async (hours-later completion), fan-out/fan-in with partial success, and compensating paths strain a linear step list. v0.1 keeps the vocabulary small and accepts reduced fidelity here; representing branching completion semantics without recreating BPMN's weight is the specification's hardest open question, and we say so rather than pretend the current shape is sufficient.

**Entry-point ambiguity.** Flow resolution at the trigger is occasionally genuinely ambiguous (one endpoint serving two business flows). Explicit client hints or upstream disambiguation are required; the spec permits `flow.id` rewriting at a declared step boundary but treats it as a smell.

**Partial adoption.** The pattern degrades gracefully — unbound components render as undeclared territory — but its strongest claims (the diagram as trustworthy incident surface) hold only for declared flows over materialized components. We consider visible incompleteness a feature (observability debt on the map); a skeptic may reasonably consider it an adoption tax.

**Evidence.** This is a pattern-and-specification paper: its claims are architectural — they follow from the properties of the declared artifacts and of standard, mature mechanisms — and feasibility is demonstrated by the runnable reference implementation, not asserted. Quantified operational claims (incident-time reduction, drift-detection yield) are deliberately not made; they require deployments of the open implementation, and we invite exactly that replication.

## 10. Conclusion

The architecture diagram and the observability platform have been describing the same system past each other. The missing artifact between them is small: a declared business flow, governed like code, whose identity rides the telemetry. With it, coverage becomes a constraint instead of a hope, drift becomes a diff instead of an audit finding, unit economics attach to business meaning, and the diagram — for decades the first casualty of production reality — becomes the one surface guaranteed to be current, because the system is materialized from it and the signals are joined to it. The specification is open; the ingredients are standard; the synthesis is available to any organization willing to treat its business flows as seriously as its infrastructure.

## Data & Code Availability

The FlowBind open specification, JSON Schemas, reference validator, and examples accompany this paper at https://github.com/azimuth-ink/flowbind and are archived on Zenodo (concept DOI 10.5281/zenodo.21524083, resolving to the latest version). This paper builds on and extends the author's prior publication [Gray 2026]. Code: Apache-2.0. Paper: CC BY 4.0.

## Acknowledgments

Drafting and specification development were assisted by Claude (Anthropic); all design decisions, claims, and errors are the author's.

## References

- Beyer, B., Jones, C., Petoff, J., Murphy, N.R. (eds.) (2016). *Site Reliability Engineering: How Google Runs Production Systems.* O'Reilly.
- Brown, S. *The C4 Model for Visualising Software Architecture.* c4model.com.
- Gebru, T., et al. (2021). Datasheets for Datasets. *Communications of the ACM*, 64(12).
- Gray, J. (2026). Flow-Based Telemetry Coverage: A Method for Measuring and Governing Observability by Business-Flow Consequence. Zenodo. https://doi.org/10.5281/zenodo.21415948
- ISO/IEC/IEEE (2022). *ISO/IEC/IEEE 42010: Software, systems and enterprise — Architecture description.*
- Kruchten, P. (1995). The 4+1 View Model of Architecture. *IEEE Software*, 12(6).
- Murphy, G.C., Notkin, D., Sullivan, K.J. (2001). Software Reflexion Models: Bridging the Gap Between Design and Implementation. *IEEE Transactions on Software Engineering*, 27(4).
- OpenTelemetry Authors. *OpenTelemetry Specification and Semantic Conventions.* opentelemetry.io.
- Torres-Arias, S., et al. (2019). in-toto: Providing Farm-to-Table Guarantees for Bits and Bytes. *USENIX Security Symposium.*
- van der Aalst, W.M.P. (2016). *Process Mining: Data Science in Action* (2nd ed.). Springer.
- SLSA: Supply-chain Levels for Software Artifacts, v1.0. slsa.dev.
- Kiali Project. *Service Mesh Observability for Istio.* kiali.io.
- Mitchell, M., et al. (2019). Model Cards for Model Reporting. *ACM FAT\*.*
