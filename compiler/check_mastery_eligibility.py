import argparse
from compiler.common import validate_graph, validate_evidence, validate_execution, validate_policy, ValidationError
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
        ev = validate_evidence()["evidence"]
        ex = validate_execution()["execution"]
        validate_policy()
        accepted = [r for r in ev["evidence_records"] if r.get("node_id") == args.node_id and r.get("status") == "accepted"]
        completed_reviews = [r for r in ex["reviews"] if r.get("node_id") == args.node_id and r.get("status") == "completed"]
        missing = []
        if node.get("state") not in {"passed", "mastered"}:
            missing.append("Node must be passed before mastery can be considered.")
        if not accepted:
            missing.append("Requires at least one accepted evidence record.")
        if not completed_reviews:
            missing.append("Requires at least one completed review.")
        print(f"Node: {args.node_id}")
        print(f"Eligible for mastery: {len(missing) == 0}")
        if missing:
            print()
            print("Missing:")
            for item in missing:
                print(f"- {item}")
        print()
        print("Warnings:")
        print("- Explicit user confirmation is required before mastery transition.")
    except ValidationError as exc:
        print(f"[INVALID MASTERY CHECK] {exc}")
        raise SystemExit(1)
if __name__ == "__main__": main()
