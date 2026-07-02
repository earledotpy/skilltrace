from compiler.common import validate_graph, validate_evidence, validate_execution, recommend_nodes, ValidationError
def main():
    try:
        g = validate_graph()
        ev = validate_evidence()["evidence"]
        ex = validate_execution()["execution"]
        print("Skill Graph Home")
        print("================")
        print()
        print("Graph")
        print("-----")
        for state, count in sorted(g["state_counts"].items()):
            print(f"{state}: {count}")
        print()
        print("Evidence")
        print("--------")
        print(f"artifact_specs: {len(ev['artifact_specs'])}")
        print(f"validation_gates: {len(ev['validation_gates'])}")
        print(f"evidence_records: {len(ev['evidence_records'])}")
        print()
        print("Execution")
        print("---------")
        print(f"sessions: {len(ex['sessions'])}")
        print(f"open_blockers: {len([b for b in ex['blockers'] if b.get('status') == 'open'])}")
        print(f"scheduled_reviews: {len([r for r in ex['reviews'] if r.get('status') == 'scheduled'])}")
        print()
        print("Recommended next")
        print("----------------")
        for idx, rec in enumerate(recommend_nodes(limit=3), start=1):
            node = rec["node"]
            print(f"{idx}. {node['id']} — {node.get('title')}")
    except ValidationError as exc:
        print(f"[INVALID HOME VIEW] {exc}")
        raise SystemExit(1)
if __name__ == "__main__": main()
