import argparse
from compiler.common import validate_graph, load_evidence, load_execution, ValidationError
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("node_id")
    args = parser.parse_args()
    try:
        g = validate_graph()
        nodes = {n["id"]: n for n in g["nodes"]}
        if args.node_id not in nodes:
            raise ValidationError(f"Node not found: {args.node_id}")
        node = nodes[args.node_id]
        ev = load_evidence()
        ex = load_execution()
        print(node.get("title"))
        print("=" * len(node.get("title", "")))
        print(f"ID: {node['id']}")
        print(f"State: {node.get('state')}")
        print(f"Domain: {node.get('domain')}")
        print(f"Track: {node.get('track')}")
        print()
        print("Summary")
        print("-------")
        print(node.get("summary"))
        print()
        print("Evidence required")
        print("-----------------")
        specs = [s for s in ev["artifact_specs"] if s.get("node_id") == args.node_id]
        print(f"Artifact specs: {len(specs)}")
        for s in specs:
            print(f"- {s.get('id')}: {s.get('acceptance_summary')}")
        gates = [g for g in ev["validation_gates"] if g.get("node_id") == args.node_id]
        print(f"Validation gates: {len(gates)}")
        for gate in gates:
            print(f"- {gate.get('id')} ({gate.get('gate_kind')})")
        blockers = [b for b in ex["blockers"] if b.get("node_id") == args.node_id]
        print(f"Blockers: {len(blockers)}")
    except ValidationError as exc:
        print(f"[INVALID NODE DETAIL] {exc}")
        raise SystemExit(1)
if __name__ == "__main__": main()
