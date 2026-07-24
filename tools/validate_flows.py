#!/usr/bin/env python3
"""Polydiagram reference validator.

Validates flow descriptors against the Flow v0.1 JSON Schema, then applies
the referential checks the schema cannot express:

  R1  step ids unique within a flow
  R2  every `next` reference resolves to a declared step id (no self-loop)
  R3  fanout/choice steps declare `next`; sync/async steps may omit it (linear)
  R4  flow ids unique across the validated set
  R5  (with --registry) every step component resolves in the registry
  R6  reachability: every step reachable from the first step

Usage:
  validate_flows.py FLOW.yaml [FLOW2.yaml ...] [--registry registry.yaml]
  validate_flows.py --dir flows/ [--registry registry.yaml]

Exit code 0 = all valid; 1 = findings; 2 = usage/load error.
"""
import argparse
import json
import pathlib
import sys

try:
    import yaml
    from jsonschema import Draft202012Validator
except ImportError as e:  # pragma: no cover
    print(f"missing dependency: {e.name} (pip install jsonschema pyyaml)", file=sys.stderr)
    sys.exit(2)

SCHEMA_PATH = pathlib.Path(__file__).resolve().parents[1] / "spec" / "schemas" / "flow.schema.json"


def load_registry(path):
    """Registry stub: YAML with a `components:` list of namespaced ids."""
    data = yaml.safe_load(pathlib.Path(path).read_text())
    comps = set(data.get("components", []))
    if not comps:
        print(f"warning: registry {path} declares no components", file=sys.stderr)
    return comps


def check_flow(doc, path, validator, registry, findings):
    for err in sorted(validator.iter_errors(doc), key=lambda e: e.json_path):
        findings.append(f"{path}: schema: {err.json_path}: {err.message}")
    if findings:
        # Structural failures make referential checks unreliable; still try basics.
        pass
    steps = (doc.get("spec") or {}).get("steps") or []
    ids = [s.get("id") for s in steps if isinstance(s, dict)]
    dupes = {i for i in ids if ids.count(i) > 1}
    for d in sorted(dupes):
        findings.append(f"{path}: R1: duplicate step id '{d}'")
    idset = set(ids)
    for s in steps:
        if not isinstance(s, dict):
            continue
        sid, kind, nxt = s.get("id"), s.get("kind", "sync"), s.get("next")
        if nxt:
            for n in nxt:
                if n not in idset:
                    findings.append(f"{path}: R2: step '{sid}' -> unknown next '{n}'")
                if n == sid:
                    findings.append(f"{path}: R2: step '{sid}' references itself")
        if kind in ("fanout", "choice") and not nxt:
            findings.append(f"{path}: R3: {kind} step '{sid}' must declare next[]")
        if registry is not None:
            comp = s.get("component")
            if comp and comp not in registry:
                findings.append(f"{path}: R5: step '{sid}' component '{comp}' not in registry")
    # R6 reachability (linear default: step i implicitly precedes step i+1 unless next given)
    if steps and not any(f.startswith(f"{path}: R2") for f in findings):
        adj = {}
        for i, s in enumerate(steps):
            sid = s.get("id")
            adj[sid] = list(s.get("next") or ([] if i + 1 >= len(steps) else [steps[i + 1].get("id")]))
        seen, stack = set(), [steps[0].get("id")]
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            stack.extend(adj.get(cur, []))
        for sid in idset - seen:
            findings.append(f"{path}: R6: step '{sid}' unreachable from '{steps[0].get('id')}'")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("flows", nargs="*", help="flow YAML files")
    ap.add_argument("--dir", help="validate every *.flow.yaml under this directory")
    ap.add_argument("--registry", help="registry stub YAML (components: [...])")
    args = ap.parse_args()

    paths = [pathlib.Path(p) for p in args.flows]
    if args.dir:
        paths += sorted(pathlib.Path(args.dir).rglob("*.flow.yaml"))
    if not paths:
        ap.error("no flow files given")

    schema = json.loads(SCHEMA_PATH.read_text())
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    registry = load_registry(args.registry) if args.registry else None

    findings, flow_ids = [], {}
    for p in paths:
        try:
            doc = yaml.safe_load(p.read_text())
        except Exception as e:
            findings.append(f"{p}: load error: {e}")
            continue
        check_flow(doc, p, validator, registry, findings)
        fid = ((doc.get("metadata") or {}).get("id")) if isinstance(doc, dict) else None
        if fid:
            if fid in flow_ids:
                findings.append(f"{p}: R4: flow id '{fid}' already declared in {flow_ids[fid]}")
            flow_ids[fid] = p

    if findings:
        print(f"FAIL — {len(findings)} finding(s):")
        for f in findings:
            print(f"  {f}")
        return 1
    print(f"OK — {len(paths)} flow(s) valid" + (f" against registry ({len(registry)} components)" if registry else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
