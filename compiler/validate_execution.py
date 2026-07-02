from compiler.common import validate_execution, print_validation_ok, ValidationError
def main():
    try:
        ex = validate_execution()
        e = ex["execution"]
        print_validation_ok("Execution layer loaded successfully", Sessions=len(e["sessions"]), Session_work=len(e["session_work"]), Blockers=len(e["blockers"]), Remediation_actions=len(e["remediation_actions"]), Reviews=len(e["reviews"]), Events=len(e["events"]))
    except ValidationError as exc:
        print(f"[INVALID EXECUTION] {exc}")
        raise SystemExit(1)
if __name__ == "__main__": main()
