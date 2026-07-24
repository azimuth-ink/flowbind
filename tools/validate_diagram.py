#!/usr/bin/env python3
"""FlowBind diagram validator (Topology / Layer / View).

Beyond envelope schema validation, enforces:

  DG1  path hygiene: all refs repo-root-relative, no '..', no absolute, exist
  DG2  Topology: unique node/edge ids; edge from/to resolve
  DG3  Layer: annotation refs resolve to base node/edge ids; unique refs per
       section; network mtls requires certificate
  DG4  Layer: network EDGE annotations must declare protocol
  DG5  imports: fragment file+key exist; fragments are single-level (no $use
       inside a fragment); unknown $use names rejected
  DG6  merged annotation data (defaults < fragment < local, $use removed)
       validates against the domain profile (network/authn/authz built in;
       x-* via metadata.annotation_schema)
  DG7  domain 'flow' is reserved (derived projection) — authored flow layers
       rejected
  DG8  View: every layer loads, is a Layer, and shares the view's base;
       display.isolate and badge prefixes name layers in the view
  DG9  (--flows-dir) every flow step component exists as a topology node
       component — the closed-loop check

Referenced documents are fully validated transitively (memoized).
Exit 0 = valid; 1 = findings; 2 = usage/load error.
"""
import argparse
import copy
import json
import pathlib
import sys

try:
    import yaml
    from jsonschema import Draft202012Validator
except ImportError as e:  # pragma: no cover
    print(f"missing dependency: {e.name} (pip install jsonschema pyyaml)", file=sys.stderr)
    sys.exit(2)

TOOLS = pathlib.Path(__file__).resolve().parent
SCHEMA = json.loads((TOOLS.parent / "spec" / "schemas" / "diagram.schema.json").read_text())
DOMAIN_PROFILES = {
    name: {"$defs": SCHEMA["$defs"], "$ref": f"#/$defs/domain_{name}_annotation"}
    for name in ("network", "authn", "authz")
}


class Ctx:
    def __init__(self, root):
        self.root = pathlib.Path(root).resolve()
        self.findings = []
        self.cache = {}          # repo-path -> (kind, doc) for validated docs
        self.envelope = Draft202012Validator(SCHEMA)

    def fail(self, where, msg):
        self.findings.append(f"{where}: {msg}")


def safe_path(ctx, ref, where):
    if ref.startswith("/") or ".." in ref.split("/"):
        ctx.fail(where, f"DG1: illegal path '{ref}' (must be repo-root-relative, no '..')")
        return None
    p = (ctx.root / ref).resolve()
    if not str(p).startswith(str(ctx.root)):
        ctx.fail(where, f"DG1: path escapes repo root: '{ref}'")
        return None
    if not p.exists():
        ctx.fail(where, f"DG1: referenced file does not exist: '{ref}'")
        return None
    return p


def load_doc(ctx, ref, where):
    """Load, envelope-validate, and structurally validate a document (memoized)."""
    if ref in ctx.cache:
        return ctx.cache[ref]
    p = safe_path(ctx, ref, where)
    if p is None:
        return None
    try:
        doc = yaml.safe_load(p.read_text())
    except Exception as e:
        ctx.fail(ref, f"load error: {e}")
        return None
    errs = sorted(ctx.envelope.iter_errors(doc), key=lambda e: e.json_path)
    if errs:
        for e in errs[:5]:
            ctx.fail(ref, f"schema: {e.json_path}: {e.message[:110]}")
        ctx.cache[ref] = None
        return None
    kind = doc.get("kind")
    ctx.cache[ref] = (kind, doc)  # pre-cache to break accidental cycles
    if kind == "Topology":
        check_topology(ctx, ref, doc)
    elif kind == "Layer":
        check_layer(ctx, ref, doc)
    elif kind == "View":
        check_view(ctx, ref, doc)
    return ctx.cache[ref]


def check_topology(ctx, ref, doc):
    node_ids = [n["id"] for n in doc["nodes"]]
    edge_ids = [e["id"] for e in doc.get("edges", [])]
    for dup in {i for i in node_ids if node_ids.count(i) > 1}:
        ctx.fail(ref, f"DG2: duplicate node id '{dup}'")
    for dup in {i for i in edge_ids if edge_ids.count(i) > 1}:
        ctx.fail(ref, f"DG2: duplicate edge id '{dup}'")
    ns = set(node_ids)
    for e in doc.get("edges", []):
        for end in ("from", "to"):
            if e[end] not in ns:
                ctx.fail(ref, f"DG2: edge '{e['id']}' {end} '{e[end]}' is not a node")


def resolve_fragment(ctx, ref, imports, name, where):
    if name not in imports:
        ctx.fail(where, f"DG5: unknown $use '{name}'")
        return {}
    spec = imports[name]
    p = safe_path(ctx, spec["path"], where)
    if p is None:
        return {}
    try:
        frag_doc = yaml.safe_load(p.read_text()) or {}
    except Exception as e:
        ctx.fail(where, f"DG5: fragment load error: {e}")
        return {}
    frag = frag_doc.get(spec["fragment"])
    if frag is None:
        ctx.fail(where, f"DG5: fragment key '{spec['fragment']}' not in {spec['path']}")
        return {}
    if "$use" in json.dumps(frag):
        ctx.fail(where, f"DG5: fragment '{name}' is not single-level (contains $use)")
        return {}
    return copy.deepcopy(frag)


def shallow_merge(base, over):
    out = copy.deepcopy(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = shallow_merge(out[k], v)   # objects merge recursively; scalars/arrays replace
        else:
            out[k] = copy.deepcopy(v)
    return out


def check_layer(ctx, ref, doc):
    meta = doc["metadata"]
    if meta["domain"] == "flow":
        ctx.fail(ref, "DG7: domain 'flow' is reserved for the derived flow projection")
    base = load_doc(ctx, doc["base"], ref)
    if base is None or base[0] != "Topology":
        if base is not None:
            ctx.fail(ref, f"DG3: base '{doc['base']}' is kind {base[0]}, expected Topology")
        return
    topo = base[1]
    node_ids = {n["id"] for n in topo["nodes"]}
    edge_ids = {e["id"] for e in topo.get("edges", [])}

    profile = DOMAIN_PROFILES.get(meta["domain"])
    if profile is None and meta["domain"].startswith("x-"):
        aspath = meta.get("annotation_schema")
        if not aspath:
            ctx.fail(ref, f"DG6: x- domain '{meta['domain']}' requires metadata.annotation_schema")
        else:
            p = safe_path(ctx, aspath, ref)
            if p is not None:
                profile = json.loads(p.read_text())
    pval = Draft202012Validator(profile) if profile else None
    imports = doc.get("imports", {})
    defaults = doc.get("defaults", {})

    for section, idset in (("node_annotations", node_ids), ("edge_annotations", edge_ids)):
        seen = set()
        for ann in doc.get(section, []):
            where = f"{ref}[{section}:{ann['ref']}]"
            if ann["ref"] in seen:
                ctx.fail(where, "DG3: duplicate annotation ref in section")
            seen.add(ann["ref"])
            if ann["ref"] not in idset:
                ctx.fail(where, f"DG3: '{ann['ref']}' not in base {section.split('_')[0]} ids")
            data = copy.deepcopy(ann["data"])
            use = data.pop("$use", None)
            merged = defaults
            if use is not None:
                merged = shallow_merge(merged, resolve_fragment(ctx, ref, imports, use, where))
            merged = shallow_merge(merged, data)
            if pval is not None:
                for e in sorted(pval.iter_errors(merged), key=lambda e: e.json_path):
                    ctx.fail(where, f"DG6: {e.json_path}: {e.message[:110]}")
            if meta["domain"] == "network":
                tls = merged.get("tls") or {}
                if tls.get("mode") == "mtls" and "certificate" not in tls:
                    ctx.fail(where, "DG3: tls.mode=mtls requires tls.certificate")
                if section == "edge_annotations" and "protocol" not in merged:
                    ctx.fail(where, "DG4: network edge annotation must declare protocol")


def check_view(ctx, ref, doc):
    base = load_doc(ctx, doc["base"], ref)
    layer_ids = set()
    for lref in doc["layers"]:
        layer = load_doc(ctx, lref, ref)
        if layer is None:
            continue
        if layer[0] != "Layer":
            ctx.fail(ref, f"DG8: '{lref}' is kind {layer[0]}, expected Layer")
            continue
        layer_ids.add(layer[1]["metadata"]["id"])
        if layer[1]["base"] != doc["base"]:
            ctx.fail(ref, f"DG8: layer '{lref}' base '{layer[1]['base']}' != view base '{doc['base']}'")
    disp = doc.get("display", {})
    iso = disp.get("isolate")
    if iso and iso not in layer_ids:
        ctx.fail(ref, f"DG8: display.isolate '{iso}' is not a layer in this view")
    for badge in (disp.get("edge_badges", []) + disp.get("node_badges", [])):
        lid = badge.split(":", 1)[0]
        if lid not in layer_ids:
            ctx.fail(ref, f"DG8: badge '{badge}' references unknown layer '{lid}'")
    _ = base  # base fully validated via load_doc


def cross_check_flows(ctx, flows_dir):
    """DG9: every flow step component appears as some topology node component."""
    topo_components = set()
    for _, entry in ctx.cache.items():
        if entry and entry[0] == "Topology":
            topo_components |= {n["component"] for n in entry[1]["nodes"]}
    if not topo_components:
        return
    for fp in sorted(pathlib.Path(flows_dir).rglob("*.flow.yaml")):
        try:
            fdoc = yaml.safe_load(fp.read_text())
        except Exception:
            continue
        for step in ((fdoc.get("spec") or {}).get("steps") or []):
            comp = step.get("component")
            if comp and comp not in topo_components:
                ctx.fail(str(fp), f"DG9: flow step '{step.get('id')}' component '{comp}' has no topology node")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("docs", nargs="+", help="Topology/Layer/View YAML files (repo-root-relative)")
    ap.add_argument("--root", default=".", help="repo root that all refs resolve against")
    ap.add_argument("--flows-dir", help="cross-check flow components against validated topologies (DG9)")
    args = ap.parse_args()

    ctx = Ctx(args.root)
    for d in args.docs:
        rel = str(pathlib.Path(d))
        load_doc(ctx, rel, "<cli>")
    if args.flows_dir:
        cross_check_flows(ctx, args.flows_dir)

    if ctx.findings:
        print(f"FAIL — {len(ctx.findings)} finding(s):")
        for f in ctx.findings:
            print(f"  {f}")
        return 1
    kinds = [v[0] for v in ctx.cache.values() if v]
    print(f"OK — {len(kinds)} document(s) valid "
          f"({kinds.count('Topology')} topology, {kinds.count('Layer')} layer, {kinds.count('View')} view)"
          + (" + flow cross-check" if args.flows_dir else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
