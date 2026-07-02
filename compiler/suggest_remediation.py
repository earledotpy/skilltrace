from compiler.common import validate_execution, validate_evidence, validate_policy, ValidationError
def main():
    try:
        validate_policy()
        ex = validate_execution()["execution"]
        ev = validate_evidence()["evidence"]
        print("Remediation Suggestions")
        print("=======================")
        suggestions = []
        for b in ex["blockers"]:
            if b.get("status") == "open":
                suggestions.append((b.get("node_id"), "open_blocker", b.get("title", "Open blocker")))
        for a in ev["attempts"]:
            if a.get("status") == "failed":
                suggestions.append((a.get("node_id"), "failed_attempt", "Failed attempt remediation"))
        if not suggestions:
            print("No remediation suggestions.")
            return
        for node_id, trigger, title in suggestions:
            print(f"- {title}: {node_id} ({trigger})")
    except ValidationError as exc:
        print(f"[INVALID REMEDIATION SUGGESTION] {exc}")
        raise SystemExit(1)
if __name__ == "__main__": main()
