import argparse
from compiler.common import validate_graph, validate_evidence, ValidationError
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--node-id", default=None)
    args = parser.parse_args()
    try:
        ev = validate_evidence()
        nodes = ev["graph"]["nodes"]
        evidence = ev["evidence"]
        node_ids = [args.node_id] if args.node_id else [n["id"] for n in nodes]
        print("Evidence Status")
        print("===============")
        for node_id in node_ids:
            specs = [s for s in evidence["artifact_specs"] if s.get("node_id") == node_id]
            gates = [g for g in evidence["validation_gates"] if g.get("node_id") == node_id]
            records = [r for r in evidence["evidence_records"] if r.get("node_id") == node_id]
            print()
            print(node_id)
            print("-" * len(node_id))
            print(f"Artifact specs: {len(specs)}")
            print(f"Validation gates: {len(gates)}")
            print(f"Evidence records: {len(records)}")
            print(f"Accepted evidence: {len([r for r in records if r.get('status') == 'accepted'])}")
    except ValidationError as exc:
        print(f"[INVALID EVIDENCE STATUS] {exc}")
        raise SystemExit(1)
if __name__ == "__main__": main()
