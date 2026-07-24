# Flow Descriptor v0.1

Normative definition: [`schemas/flow.schema.json`](schemas/flow.schema.json)
(JSON Schema 2020-12). Design rationale and full context: paper §3–§4.

A **Flow** declares one business-meaningful path over a typed component graph.
It references components; it never restates the graph.

| Section | Purpose |
|---|---|
| `metadata` | identity, semver, dual ownership (business + technical), criticality tier |
| `spec.trigger` | how the flow begins (`http`, `event`, `schedule`, `user_interaction`) |
| `spec.steps` | ordered steps: component, operation, kind (`sync`/`async`/`fanout`/`choice`), optional `next[]` for branching |
| `spec.slos` | end-to-end objectives; `latency_p95_ms` measures to the synchronous frontier |
| `spec.telemetry` | required signal set, attribute namespace, sampling floor |

**Telemetry binding contract.** At the trigger, the entry component stamps
`flow.id`, `flow.version`, `flow.step` into trace context/baggage; each
declared step's hosting component updates `flow.step` on its boundary span.
See `examples/telemetry-binding.md` for the attribute table and a worked
coverage query.

**Validator-enforced rules (beyond schema):** step-id uniqueness (R1),
`next` referential integrity (R2), `next` required for fanout/choice (R3),
flow-id uniqueness across the set (R4), component resolution against the
registry (R5), reachability (R6).

**Open questions (tracked):** branching completion semantics for long-gap
async and fan-in with partial success; multi-flow entry-point disambiguation.
