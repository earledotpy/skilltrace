from compiler.common import validate_graph, validate_evidence, validate_execution, validate_interface, validate_policy, validate_release, ValidationError
def main():
    print("System Health")
    print("=============")
    try:
        validate_graph(); print("[OK] Graph layer")
        validate_evidence(); print("[OK] Evidence layer")
        validate_execution(); print("[OK] Execution layer")
        validate_interface(); print("[OK] Interface layer")
        validate_policy(); print("[OK] Policy layer")
        validate_release(); print("[OK] Release layer")
        print()
        print("Status: healthy")
    except ValidationError as exc:
        print(f"[FAIL] {exc}")
        raise SystemExit(1)
if __name__ == "__main__": main()
