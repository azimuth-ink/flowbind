# Telemetry Binding Conventions (flow.* attributes)

Expressed as an OpenTelemetry semantic-convention extension; nothing here
requires proprietary agents.

| Attribute | Type | Set by | Meaning |
|---|---|---|---|
| `flow.id` | string | entry component at trigger | declared flow id (`metadata.id`) |
| `flow.version` | string | entry component | flow semver at execution time |
| `flow.step` | string | hosting component, boundary span | current declared step id |

**Propagation:** carry the three attributes in context/baggage; record on
every span; attach as exemplar labels on metrics; include on cost/usage
ledger records. Interior spans inherit; only declared-step boundaries update.

**Coverage constraint (paper §4.2):** for flow F over window W, every declared
step must appear in signals of F's `required_signals`, and effective sampling
must be ≥ `sampling_floor`.

Worked query sketch (trace store, pseudo-SQL):

```sql
SELECT s.step_id
FROM   declared_steps('quote-issue') s
LEFT JOIN spans t
  ON  t.attr['flow.id']   = 'quote-issue'
  AND t.attr['flow.step'] = s.step_id
  AND t.start >= now() - INTERVAL '7 days'
GROUP BY s.step_id
HAVING count(t.span_id) = 0;   -- rows returned = named blind spots
```

**Cardinality note:** `flow.id`/`flow.step` are low-cardinality by
construction — flows are curated, reviewed artifacts (dozens, not thousands).
That governance commitment is what keeps this binding cheap.
