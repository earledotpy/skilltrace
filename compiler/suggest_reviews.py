from compiler.common import validate_graph, validate_execution, validate_policy, ValidationError
def main():
    try:
        validate_policy()
        g = validate_graph()
        ex = validate_execution()["execution"]
        existing = {(r.get("node_id"), str(r.get("scheduled_for"))) for r in ex["reviews"]}
        print("Review Suggestions")
        print("==================")
        passed = [n for n in g["nodes"] if n.get("state") in {"passed", "mastered"}]
        if not passed:
            print("No review suggestions.")
            return
        for node in passed:
            print(f"- {node['id']}: schedule spaced recall review")
    except ValidationError as exc:
        print(f"[INVALID REVIEW SUGGESTION] {exc}")
        raise SystemExit(1)
if __name__ == "__main__": main()
